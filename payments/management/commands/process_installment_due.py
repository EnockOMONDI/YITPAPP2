"""
Django Management Command: Process Installment Due
Automated task to process installment due dates and manage payment sequences
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

from users.models import Profile
from payments.models import Payment
from payments.payment_service import PaymentService
from payments.email_service import PaymentEmailService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process installment due dates and manage payment sequences'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to the database',
        )
        parser.add_argument(
            '--check-overdue',
            action='store_true',
            help='Check for overdue installments and send notifications',
        )
        parser.add_argument(
            '--auto-expire',
            action='store_true',
            help='Automatically expire overdue installments',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.check_overdue = options['check_overdue']
        self.auto_expire = options['auto_expire']
        self.verbose = options['verbose']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No changes will be made to the database')
            )
        
        self.stdout.write(
            self.style.SUCCESS('💳 Starting installment due processing...')
        )
        
        try:
            # Process upcoming due dates
            upcoming_due = self.process_upcoming_due_dates()
            
            # Check overdue installments if requested
            overdue_processed = 0
            if self.check_overdue:
                overdue_processed = self.process_overdue_installments()
            
            # Auto-expire if requested
            expired_count = 0
            if self.auto_expire:
                expired_count = self.auto_expire_overdue_installments()
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Installment due processing completed:\n'
                    f'   • Upcoming due notifications: {upcoming_due}\n'
                    f'   • Overdue installments processed: {overdue_processed}\n'
                    f'   • Auto-expired installments: {expired_count}'
                )
            )
            
        except Exception as e:
            logger.error(f"Installment due processing failed: {str(e)}")
            raise CommandError(f'Installment due processing failed: {str(e)}')

    def process_upcoming_due_dates(self):
        """Process upcoming installment due dates and send notifications"""
        now = timezone.now()
        notifications_sent = 0
        
        # Find partial payments approaching expiry (3 days, 1 day)
        warning_intervals = [3, 1]
        
        for days in warning_intervals:
            due_date = now + timedelta(days=days)
            
            profiles = Profile.objects.filter(
                payment_status='partially_paid',
                payment_expiration_date__date=due_date.date()
            )
            
            if self.verbose:
                self.stdout.write(f'Found {profiles.count()} profiles with installments due in {days} days')
            
            for profile in profiles:
                if self.verbose:
                    self.stdout.write(f'  Processing due date notification: {profile.user.email}')
                
                if not self.dry_run:
                    notification_sent = self.send_due_date_notification(profile, days)
                    if notification_sent:
                        notifications_sent += 1
        
        return notifications_sent

    def process_overdue_installments(self):
        """Process overdue installments and send notifications"""
        now = timezone.now()
        overdue_processed = 0
        
        # Find profiles with overdue installments (past expiration date but still partially_paid)
        overdue_profiles = Profile.objects.filter(
            payment_status='partially_paid',
            payment_expiration_date__lt=now
        )
        
        if self.verbose:
            self.stdout.write(f'Found {overdue_profiles.count()} overdue installments')
        
        for profile in overdue_profiles:
            days_overdue = (now - profile.payment_expiration_date).days
            
            if self.verbose:
                self.stdout.write(f'  Processing overdue installment: {profile.user.email} ({days_overdue} days overdue)')
            
            if not self.dry_run:
                # Send overdue notification
                notification_sent = self.send_overdue_notification(profile, days_overdue)
                if notification_sent:
                    overdue_processed += 1
        
        return overdue_processed

    def auto_expire_overdue_installments(self):
        """Automatically expire installments that are significantly overdue"""
        now = timezone.now()
        expired_count = 0
        
        # Auto-expire installments that are more than 7 days overdue
        auto_expire_threshold = now - timedelta(days=7)
        
        profiles_to_expire = Profile.objects.filter(
            payment_status='partially_paid',
            payment_expiration_date__lt=auto_expire_threshold
        )
        
        if self.verbose:
            self.stdout.write(f'Found {profiles_to_expire.count()} installments to auto-expire')
        
        for profile in profiles_to_expire:
            days_overdue = (now - profile.payment_expiration_date).days
            
            if self.verbose:
                self.stdout.write(f'  Auto-expiring installment: {profile.user.email} ({days_overdue} days overdue)')
            
            if not self.dry_run:
                with transaction.atomic():
                    # Update profile status to expired
                    profile.payment_status = 'expired'
                    profile.save(update_fields=['payment_status'])
                    
                    # Send expiry notification
                    self.send_auto_expiry_notification(profile, days_overdue)
                    
                    # Log the action
                    logger.info(f"Auto-expired installment for {profile.user.email} - {days_overdue} days overdue")
                    
                    expired_count += 1
        
        return expired_count

    def send_due_date_notification(self, profile, days_until_due):
        """Send due date notification to user"""
        try:
            # Use expiry warning email for due date notifications
            return PaymentEmailService.send_expiry_warning_email(profile, days_until_due)
        except Exception as e:
            logger.error(f"Failed to send due date notification to {profile.user.email}: {str(e)}")
            return False

    def send_overdue_notification(self, profile, days_overdue):
        """Send overdue notification to user"""
        try:
            # Calculate days since payment for installment reminder
            days_since_payment = (timezone.now() - profile.partial_payment_date).days
            return PaymentEmailService.send_enhanced_installment_reminder(profile, days_since_payment)
        except Exception as e:
            logger.error(f"Failed to send overdue notification to {profile.user.email}: {str(e)}")
            return False

    def send_auto_expiry_notification(self, profile, days_overdue):
        """Send auto-expiry notification to user"""
        try:
            # Use renewal reminder for auto-expiry notifications
            return PaymentEmailService.send_renewal_reminder_email(profile, days_overdue)
        except Exception as e:
            logger.error(f"Failed to send auto-expiry notification to {profile.user.email}: {str(e)}")
            return False
