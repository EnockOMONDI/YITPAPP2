"""
Django management command to send verification reminder emails to unverified users
Usage: python manage.py send_verification_reminders
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction, models
from datetime import timedelta
import logging

from users.models import Profile, OTPVerification
from users.email_utils import send_verification_reminder_email, send_html_email, generate_otp

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send verification reminder emails to unverified users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually sending emails',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send reminders even if not due (for testing)',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Send reminder to specific user ID only',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        specific_user_id = options['user_id']

        self.stdout.write(
            self.style.SUCCESS('🔍 YITP VERIFICATION REMINDER SYSTEM')
        )
        self.stdout.write('=' * 60)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 DRY RUN MODE - No emails will be sent')
            )
        
        # Get users who need verification reminders
        users_needing_reminders = self.get_users_needing_reminders(specific_user_id, force)
        
        if not users_needing_reminders:
            self.stdout.write(
                self.style.SUCCESS('✅ No users need verification reminders at this time')
            )
            return

        self.stdout.write(
            f'📧 Found {len(users_needing_reminders)} users needing reminders'
        )

        # Process each user
        sent_count = 0
        failed_count = 0
        skipped_count = 0

        for user_data in users_needing_reminders:
            user = user_data['user']
            profile = user_data['profile']
            otp_code = user_data['otp_code']
            reminder_count = profile.verification_reminder_count + 1

            self.stdout.write(f'\n📤 Processing: {user.email}')
            self.stdout.write(f'   Reminder #{reminder_count}')
            self.stdout.write(f'   Registered: {user.date_joined.strftime("%Y-%m-%d %H:%M")}')

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f'   🧪 Would send reminder email with OTP: {otp_code}')
                )
                skipped_count += 1
                continue

            # Send reminder email
            try:
                with transaction.atomic():
                    email_sent = send_verification_reminder_email(
                        user=user,
                        otp_code=otp_code,
                        reminder_count=reminder_count
                    )

                    if email_sent:
                        # Record the reminder
                        profile.record_reminder_sent()
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✅ Reminder email sent successfully')
                        )
                        sent_count += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'   ❌ Failed to send reminder email')
                        )
                        failed_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error sending reminder: {str(e)}')
                )
                failed_count += 1
                logger.error(f"Error sending verification reminder to {user.email}: {str(e)}")

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS('📊 VERIFICATION REMINDER SUMMARY')
        )
        self.stdout.write('=' * 60)
        
        if dry_run:
            self.stdout.write(f'🧪 Dry run completed')
            self.stdout.write(f'📧 Would send: {len(users_needing_reminders)} reminders')
        else:
            self.stdout.write(f'✅ Sent: {sent_count} reminders')
            self.stdout.write(f'❌ Failed: {failed_count} reminders')
            self.stdout.write(f'⏭️ Skipped: {skipped_count} reminders')

            # Send admin summary if any emails were sent
            if sent_count > 0:
                self.send_admin_summary(sent_count, failed_count)

    def get_users_needing_reminders(self, specific_user_id=None, force=False):
        """Get list of users who need verification reminders"""
        users_needing_reminders = []

        if specific_user_id:
            # Process specific user only
            try:
                user = User.objects.get(id=specific_user_id)
                profile, created = Profile.objects.get_or_create(user=user)
                
                if force or profile.needs_verification_reminder():
                    otp_code = self.get_or_create_otp(user)
                    if otp_code:
                        users_needing_reminders.append({
                            'user': user,
                            'profile': profile,
                            'otp_code': otp_code
                        })
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ User with ID {specific_user_id} not found')
                )
        else:
            # Get all users who need reminders
            # Include both inactive users and active users who aren't email verified
            target_users = User.objects.filter(
                models.Q(is_active=False) | 
                models.Q(profile__email_verified=False)
            ).exclude(
                profile__reminder_emails_stopped=True
            ).select_related('profile')

            for user in target_users:
                # Ensure user has a profile
                profile, created = Profile.objects.get_or_create(user=user)
                
                # Check if reminder is needed
                if force or profile.needs_verification_reminder():
                    # Get or create fresh OTP
                    otp_code = self.get_or_create_otp(user)
                    if otp_code:
                        users_needing_reminders.append({
                            'user': user,
                            'profile': profile,
                            'otp_code': otp_code
                        })

        return users_needing_reminders

    def get_or_create_otp(self, user):
        """Get existing valid OTP or create new one"""
        from django.conf import settings
        
        # Check for existing valid OTP
        current_time = timezone.now()
        valid_otp = OTPVerification.objects.filter(
            user=user,
            is_used=False,
            is_verified=False,
            expires_at__gt=current_time
        ).order_by('-created_at').first()

        if valid_otp:
            return valid_otp.otp_code

        # Create new OTP
        try:
            # Invalidate old OTPs
            OTPVerification.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Generate new OTP
            otp_code = generate_otp(length=getattr(settings, 'OTP_LENGTH', 6))
            expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 200)
            expires_at = current_time + timedelta(minutes=expiry_minutes)
            
            # Create OTP record
            OTPVerification.objects.create(
                user=user,
                otp_code=otp_code,
                expires_at=expires_at
            )
            
            return otp_code
            
        except Exception as e:
            logger.error(f"Failed to create OTP for user {user.email}: {str(e)}")
            return None

    def send_admin_summary(self, sent_count, failed_count):
        """Send daily summary to admin"""
        try:
            from django.conf import settings
            from django.template.loader import render_to_string
            
            context = {
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total_count': sent_count + failed_count,
                'date': timezone.now().strftime('%Y-%m-%d'),
                'site_name': 'Youth Impact Training Programme'
            }

            subject = f"YITP Daily Verification Reminders Summary - {context['date']}"
            
            # Simple email content
            message = f"""
YITP Verification Reminders Daily Summary
Date: {context['date']}

✅ Successfully sent: {sent_count} reminders
❌ Failed to send: {failed_count} reminders
📊 Total processed: {sent_count + failed_count} reminders

This is an automated summary from the YITP verification reminder system.
            """

            from users.email_utils import send_html_email
            send_html_email(
                subject=subject,
                html_content=message.replace('\n', '<br>'),
                recipient_list=[settings.ADMIN_EMAIL],
                plain_text_content=message
            )
            
            self.stdout.write(
                self.style.SUCCESS('📧 Admin summary email sent')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send admin summary: {str(e)}')
            )
            logger.error(f"Failed to send admin summary: {str(e)}")
