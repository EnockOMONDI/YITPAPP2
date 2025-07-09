"""
Django Management Command: Send Renewal Reminders
Automated task to send payment renewal reminders and second installment notifications
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

from users.models import Profile
from payments.models import Payment, PaymentNotification
from payments.email_service import PaymentEmailService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send payment renewal reminders and second installment notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without sending emails or making database changes',
        )
        parser.add_argument(
            '--type',
            choices=['installment', 'renewal', 'all'],
            default='all',
            help='Type of reminders to send (default: all)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.reminder_type = options['type']
        self.verbose = options['verbose']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No emails will be sent')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'📧 Starting renewal reminders ({self.reminder_type})...')
        )
        
        try:
            installment_reminders = 0
            renewal_reminders = 0
            
            if self.reminder_type in ['installment', 'all']:
                installment_reminders = self.send_installment_reminders()
            
            if self.reminder_type in ['renewal', 'all']:
                renewal_reminders = self.send_renewal_reminders()
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Renewal reminders completed:\n'
                    f'   • Installment reminders sent: {installment_reminders}\n'
                    f'   • Renewal reminders sent: {renewal_reminders}'
                )
            )
            
        except Exception as e:
            logger.error(f"Renewal reminders failed: {str(e)}")
            raise CommandError(f'Renewal reminders failed: {str(e)}')

    def send_installment_reminders(self):
        """Send second installment reminders to users with partial payments"""
        now = timezone.now()
        reminders_sent = 0
        
        # Find profiles with partial payments that need reminders
        # Send reminders at different intervals: 7 days, 14 days, 21 days, 28 days
        reminder_intervals = [7, 14, 21, 28]
        
        for days in reminder_intervals:
            target_date = now - timedelta(days=days)
            
            profiles = Profile.objects.filter(
                payment_status='partially_paid',
                partial_payment_date__date=target_date.date()
            )
            
            if self.verbose:
                self.stdout.write(f'Found {profiles.count()} profiles for {days}-day installment reminder')
            
            for profile in profiles:
                # Check if reminder already sent for this interval
                if self.has_installment_reminder_been_sent(profile, days):
                    if self.verbose:
                        self.stdout.write(f'  Skipping {profile.user.email} - reminder already sent')
                    continue
                
                if self.verbose:
                    self.stdout.write(f'  Sending {days}-day installment reminder: {profile.user.email}')
                
                if not self.dry_run:
                    email_sent = self.send_installment_reminder_email(profile, days)
                    if email_sent:
                        self.record_installment_reminder_sent(profile, days)
                        reminders_sent += 1
        
        return reminders_sent

    def send_renewal_reminders(self):
        """Send renewal reminders to users with expired payments"""
        now = timezone.now()
        reminders_sent = 0
        
        # Find profiles with expired payments that need renewal reminders
        # Send reminders at 1 day, 7 days, 30 days after expiry
        reminder_intervals = [1, 7, 30]
        
        for days in reminder_intervals:
            target_date = now - timedelta(days=days)
            
            profiles = Profile.objects.filter(
                payment_status='expired',
                payment_expiration_date__date=target_date.date()
            )
            
            if self.verbose:
                self.stdout.write(f'Found {profiles.count()} profiles for {days}-day renewal reminder')
            
            for profile in profiles:
                # Check if reminder already sent for this interval
                if self.has_renewal_reminder_been_sent(profile, days):
                    if self.verbose:
                        self.stdout.write(f'  Skipping {profile.user.email} - reminder already sent')
                    continue
                
                if self.verbose:
                    self.stdout.write(f'  Sending {days}-day renewal reminder: {profile.user.email}')
                
                if not self.dry_run:
                    email_sent = self.send_renewal_reminder_email(profile, days)
                    if email_sent:
                        self.record_renewal_reminder_sent(profile, days)
                        reminders_sent += 1
        
        return reminders_sent

    def has_installment_reminder_been_sent(self, profile, days):
        """Check if installment reminder has already been sent for this interval"""
        # This would check a tracking table or field
        # For now, return False to allow sending
        return False

    def has_renewal_reminder_been_sent(self, profile, days):
        """Check if renewal reminder has already been sent for this interval"""
        # This would check a tracking table or field
        # For now, return False to allow sending
        return False

    def send_installment_reminder_email(self, profile, days_since_payment):
        """Send installment reminder email to user"""
        try:
            # Use the enhanced email service
            return PaymentEmailService.send_enhanced_installment_reminder(profile, days_since_payment)
        except Exception as e:
            logger.error(f"Failed to send installment reminder email to {profile.user.email}: {str(e)}")
            return False

    def send_renewal_reminder_email(self, profile, days_since_expiry):
        """Send renewal reminder email to user"""
        try:
            # Use the enhanced email service
            return PaymentEmailService.send_renewal_reminder_email(profile, days_since_expiry)
        except Exception as e:
            logger.error(f"Failed to send renewal reminder email to {profile.user.email}: {str(e)}")
            return False

    def record_installment_reminder_sent(self, profile, days):
        """Record that installment reminder was sent"""
        # This would record in a tracking table
        logger.info(f"Installment reminder recorded for {profile.user.email} - {days} days")

    def record_renewal_reminder_sent(self, profile, days):
        """Record that renewal reminder was sent"""
        # This would record in a tracking table
        logger.info(f"Renewal reminder recorded for {profile.user.email} - {days} days")
