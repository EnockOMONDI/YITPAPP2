"""
Django Management Command: Check Payment Expiry
Automated task to check for expired payments and partial payment access
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

from payments.models import Payment
from users.models import Profile
from payments.email_service import PaymentEmailService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for expired payments and partial payment access, update statuses and send notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to the database',
        )
        parser.add_argument(
            '--send-warnings',
            action='store_true',
            help='Send expiry warning emails (7-day and 1-day warnings)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.send_warnings = options['send_warnings']
        self.verbose = options['verbose']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No changes will be made to the database')
            )
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting payment expiry check...')
        )
        
        try:
            # Check and expire pending payments
            expired_payments = self.check_pending_payment_expiry()
            
            # Check and expire partial payment access
            expired_partial_payments = self.check_partial_payment_expiry()
            
            # Send expiry warnings if requested
            warnings_sent = 0
            if self.send_warnings:
                warnings_sent = self.send_expiry_warnings()
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Payment expiry check completed:\n'
                    f'   • Expired pending payments: {expired_payments}\n'
                    f'   • Expired partial payments: {expired_partial_payments}\n'
                    f'   • Warning emails sent: {warnings_sent}'
                )
            )
            
        except Exception as e:
            logger.error(f"Payment expiry check failed: {str(e)}")
            raise CommandError(f'Payment expiry check failed: {str(e)}')

    def check_pending_payment_expiry(self):
        """Check for pending payments that have expired (24 hours)"""
        now = timezone.now()
        expired_count = 0
        
        # Find pending payments older than 24 hours
        expired_payments = Payment.objects.filter(
            status='pending',
            created_at__lt=now - timedelta(hours=24)
        )
        
        if self.verbose:
            self.stdout.write(f'Found {expired_payments.count()} pending payments to expire')
        
        for payment in expired_payments:
            if self.verbose:
                self.stdout.write(f'  Expiring payment: {payment.reference_number}')
            
            if not self.dry_run:
                with transaction.atomic():
                    payment.status = 'expired'
                    payment.save(update_fields=['status'])
                    
                    # Log the expiry
                    logger.info(f"Payment expired: {payment.reference_number}")
            
            expired_count += 1
        
        return expired_count

    def check_partial_payment_expiry(self):
        """Check for partial payments that have expired (30 days)"""
        now = timezone.now()
        expired_count = 0
        
        # Find profiles with expired partial payments
        expired_profiles = Profile.objects.filter(
            payment_status='partially_paid',
            payment_expiration_date__lt=now
        )
        
        if self.verbose:
            self.stdout.write(f'Found {expired_profiles.count()} partial payments to expire')
        
        for profile in expired_profiles:
            if self.verbose:
                self.stdout.write(f'  Expiring partial payment: {profile.user.email}')
            
            if not self.dry_run:
                with transaction.atomic():
                    profile.payment_status = 'expired'
                    profile.save(update_fields=['payment_status'])
                    
                    # Log the expiry
                    logger.info(f"Partial payment expired: {profile.user.email}")
            
            expired_count += 1
        
        return expired_count

    def send_expiry_warnings(self):
        """Send expiry warning emails for partial payments"""
        now = timezone.now()
        warnings_sent = 0
        
        # 7-day warning
        seven_day_warning = now + timedelta(days=7)
        profiles_7day = Profile.objects.filter(
            payment_status='partially_paid',
            payment_expiration_date__date=seven_day_warning.date()
        )
        
        for profile in profiles_7day:
            if self.verbose:
                self.stdout.write(f'  Sending 7-day warning: {profile.user.email}')
            
            if not self.dry_run:
                email_sent = self.send_expiry_warning_email(profile, days_remaining=7)
                if email_sent:
                    warnings_sent += 1
        
        # 1-day warning
        one_day_warning = now + timedelta(days=1)
        profiles_1day = Profile.objects.filter(
            payment_status='partially_paid',
            payment_expiration_date__date=one_day_warning.date()
        )
        
        for profile in profiles_1day:
            if self.verbose:
                self.stdout.write(f'  Sending 1-day warning: {profile.user.email}')
            
            if not self.dry_run:
                email_sent = self.send_expiry_warning_email(profile, days_remaining=1)
                if email_sent:
                    warnings_sent += 1
        
        return warnings_sent

    def send_expiry_warning_email(self, profile, days_remaining):
        """Send expiry warning email to user"""
        try:
            # Use the enhanced email service
            return PaymentEmailService.send_expiry_warning_email(profile, days_remaining)
        except Exception as e:
            logger.error(f"Failed to send expiry warning email to {profile.user.email}: {str(e)}")
            return False
