"""
Django management command to fix admin-created users who bypassed OTP verification
Usage: python manage.py fix_admin_created_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

from users.models import Profile, OTPVerification
from users.email_utils import send_verification_reminder_email, generate_otp

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix admin-created users who bypassed OTP verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--send-reminders',
            action='store_true',
            help='Send verification reminder emails to fixed users',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        send_reminders = options['send_reminders']

        self.stdout.write(
            self.style.SUCCESS('🔧 FIXING ADMIN-CREATED USERS')
        )
        self.stdout.write('=' * 60)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 DRY RUN MODE - No changes will be made')
            )

        # Find users who are active but have no OTP records and no email verification
        problematic_users = User.objects.filter(
            is_active=True,
            profile__email_verified=False,
            otpverification__isnull=True
        ).distinct()

        self.stdout.write(f'🔍 Found {problematic_users.count()} users who bypassed OTP verification:')

        fixed_count = 0
        reminder_sent_count = 0

        for user in problematic_users:
            self.stdout.write(f'\n👤 User: {user.username} ({user.email})')
            self.stdout.write(f'   Joined: {user.date_joined.strftime("%Y-%m-%d %H:%M")}')
            self.stdout.write(f'   Active: {user.is_active}')
            
            try:
                profile = user.profile
                self.stdout.write(f'   Email Verified: {profile.email_verified}')
            except Profile.DoesNotExist:
                self.stdout.write('   Profile: Missing')

            if dry_run:
                self.stdout.write(
                    self.style.WARNING('   🧪 Would create OTP and optionally send reminder')
                )
                continue

            # Fix the user
            try:
                with transaction.atomic():
                    # Ensure user has a profile
                    profile, created = Profile.objects.get_or_create(user=user)
                    if created:
                        self.stdout.write('   ✅ Created missing profile')

                    # Create OTP record for this user
                    otp_code = self.create_otp_for_user(user)
                    if otp_code:
                        self.stdout.write(f'   ✅ Created OTP: {otp_code}')
                        fixed_count += 1

                        # Optionally send reminder email
                        if send_reminders:
                            email_sent = send_verification_reminder_email(
                                user=user,
                                otp_code=otp_code,
                                reminder_count=1
                            )
                            
                            if email_sent:
                                profile.record_reminder_sent()
                                self.stdout.write('   📧 Verification reminder sent')
                                reminder_sent_count += 1
                            else:
                                self.stdout.write('   ❌ Failed to send reminder email')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Error fixing user: {str(e)}')
                )
                logger.error(f"Error fixing user {user.email}: {str(e)}")

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(
            self.style.SUCCESS('📊 FIX ADMIN-CREATED USERS SUMMARY')
        )
        self.stdout.write('=' * 60)
        
        if dry_run:
            self.stdout.write(f'🧪 Dry run completed')
            self.stdout.write(f'👤 Would fix: {problematic_users.count()} users')
        else:
            self.stdout.write(f'✅ Fixed: {fixed_count} users')
            if send_reminders:
                self.stdout.write(f'📧 Reminders sent: {reminder_sent_count}')

    def create_otp_for_user(self, user):
        """Create OTP record for user who bypassed verification"""
        from django.conf import settings
        
        try:
            # Generate OTP
            otp_code = generate_otp(length=getattr(settings, 'OTP_LENGTH', 6))
            expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 200)
            expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
            
            # Create OTP record
            OTPVerification.objects.create(
                user=user,
                otp_code=otp_code,
                expires_at=expires_at,
                is_used=False,
                is_verified=False
            )
            
            return otp_code
            
        except Exception as e:
            logger.error(f"Failed to create OTP for user {user.email}: {str(e)}")
            return None
