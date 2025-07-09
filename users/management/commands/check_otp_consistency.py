"""
Django Management Command: Check OTP Database Consistency
Verify database integrity after SQLite migration and fix common issues
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from users.models import OTPVerification, Profile
from users.otp_views import check_database_consistency
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check and fix OTP database consistency issues after SQLite migration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically fix found issues',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
        parser.add_argument(
            '--cleanup-expired',
            action='store_true',
            help='Clean up expired OTP records',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.fix_issues = options['fix']
        
        self.stdout.write(
            self.style.SUCCESS('🔍 Starting OTP database consistency check...')
        )
        
        try:
            # Run consistency check
            is_consistent, result = check_database_consistency()
            
            if is_consistent:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {result}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Database consistency issues found:')
                )
                for issue in result:
                    self.stdout.write(f'   • {issue}')
            
            # Additional checks
            self.check_user_profiles()
            self.check_otp_records()
            
            if options['cleanup_expired']:
                self.cleanup_expired_otps()
            
            # Summary
            self.stdout.write(
                self.style.SUCCESS('\n📊 Database Consistency Check Summary:')
            )
            
            total_users = User.objects.count()
            total_profiles = Profile.objects.count()
            total_otps = OTPVerification.objects.count()
            active_otps = OTPVerification.objects.filter(is_used=False).count()
            
            self.stdout.write(f'   • Total Users: {total_users}')
            self.stdout.write(f'   • Total Profiles: {total_profiles}')
            self.stdout.write(f'   • Total OTP Records: {total_otps}')
            self.stdout.write(f'   • Active OTP Records: {active_otps}')
            
            if total_users == total_profiles:
                self.stdout.write(
                    self.style.SUCCESS('   ✅ All users have profiles')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Profile mismatch: {total_users - total_profiles} users missing profiles')
                )
            
        except Exception as e:
            logger.error(f"Database consistency check failed: {str(e)}")
            raise CommandError(f'Consistency check failed: {str(e)}')

    def check_user_profiles(self):
        """Check user profile consistency"""
        if self.verbose:
            self.stdout.write('Checking user profiles...')
        
        users_without_profiles = User.objects.filter(profile__isnull=True)
        
        if users_without_profiles.exists():
            count = users_without_profiles.count()
            self.stdout.write(
                self.style.WARNING(f'   ⚠️ Found {count} users without profiles')
            )
            
            if self.fix_issues:
                self.stdout.write('   🔧 Creating missing profiles...')
                created_count = 0
                
                for user in users_without_profiles:
                    try:
                        Profile.objects.create(user=user)
                        created_count += 1
                        if self.verbose:
                            self.stdout.write(f'      ✓ Created profile for {user.username}')
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'      ✗ Failed to create profile for {user.username}: {str(e)}')
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Created {created_count} missing profiles')
                )
        else:
            if self.verbose:
                self.stdout.write('   ✅ All users have profiles')

    def check_otp_records(self):
        """Check OTP record consistency"""
        if self.verbose:
            self.stdout.write('Checking OTP records...')
        
        # Check for orphaned OTP records
        orphaned_otps = OTPVerification.objects.filter(user__isnull=True)
        if orphaned_otps.exists():
            count = orphaned_otps.count()
            self.stdout.write(
                self.style.WARNING(f'   ⚠️ Found {count} orphaned OTP records')
            )
            
            if self.fix_issues:
                orphaned_otps.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Deleted {count} orphaned OTP records')
                )
        
        # Check for duplicate OTP codes
        from django.db.models import Count
        duplicate_otps = OTPVerification.objects.values('user', 'otp_code').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicate_otps.exists():
            count = duplicate_otps.count()
            self.stdout.write(
                self.style.WARNING(f'   ⚠️ Found {count} duplicate OTP records')
            )
            
            if self.fix_issues:
                # Keep only the most recent duplicate
                for dup in duplicate_otps:
                    user_id = dup['user']
                    otp_code = dup['otp_code']
                    
                    # Get all duplicates for this user/code combination
                    duplicates = OTPVerification.objects.filter(
                        user_id=user_id,
                        otp_code=otp_code
                    ).order_by('-created_at')
                    
                    # Delete all but the most recent
                    if duplicates.count() > 1:
                        duplicates[1:].delete()
                        if self.verbose:
                            self.stdout.write(f'      ✓ Cleaned duplicates for user {user_id}, code {otp_code}')
                
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Cleaned up duplicate OTP records')
                )
        
        if self.verbose and not orphaned_otps.exists() and not duplicate_otps.exists():
            self.stdout.write('   ✅ OTP records are consistent')

    def cleanup_expired_otps(self):
        """Clean up expired OTP records"""
        self.stdout.write('Cleaning up expired OTP records...')
        
        from django.utils import timezone
        
        expired_otps = OTPVerification.objects.filter(
            is_used=False,
            expires_at__lt=timezone.now()
        )
        
        count = expired_otps.count()
        if count > 0:
            if self.fix_issues:
                expired_otps.delete()
                self.stdout.write(
                    self.style.SUCCESS(f'   ✅ Deleted {count} expired OTP records')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️ Found {count} expired OTP records (use --fix to clean up)')
                )
        else:
            self.stdout.write('   ✅ No expired OTP records found')
