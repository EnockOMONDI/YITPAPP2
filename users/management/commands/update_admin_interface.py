"""
Management command to update admin interface with verification and location data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Profile
from django.utils import timezone


class Command(BaseCommand):
    help = 'Update admin interface with verification and location data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update-locations',
            action='store_true',
            help='Update location data from phone numbers',
        )
        parser.add_argument(
            '--verify-emails',
            action='store_true',
            help='Verify email status for users who completed OTP verification',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 YITP Admin Interface Update Tool')
        )
        self.stdout.write('=' * 50)
        
        # Update location data
        if options['update_locations']:
            self.update_locations()
        
        # Verify email status
        if options['verify_emails']:
            self.verify_email_status()
        
        # Display summary
        self.display_summary()

    def update_locations(self):
        """Update location data from phone numbers"""
        self.stdout.write('\n🌍 Updating location data...')
        
        updated_count = 0
        total_profiles = Profile.objects.count()
        
        for profile in Profile.objects.all():
            if profile.detect_and_update_location():
                updated_count += 1
                self.stdout.write(
                    f'✅ Updated location for {profile.user.username}: {profile.location_display}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📊 Location Update Summary:'
                f'\n   Total Profiles: {total_profiles}'
                f'\n   Updated Profiles: {updated_count}'
                f'\n   Success Rate: {(updated_count/total_profiles*100):.1f}%'
            )
        )

    def verify_email_status(self):
        """Verify email status for users who completed verification"""
        self.stdout.write('\n✅ Checking email verification status...')
        
        # Logic to verify email status based on OTP verification
        from users.models import OTPVerification
        
        verified_count = 0
        
        # Find users who have verified OTP but profile not marked as verified
        verified_otps = OTPVerification.objects.filter(is_verified=True)
        
        for otp in verified_otps:
            profile = getattr(otp.user, 'profile', None)
            if profile and not profile.email_verified:
                profile.email_verified = True
                profile.save(update_fields=['email_verified'])
                verified_count += 1
                self.stdout.write(
                    f'✅ Verified email for {otp.user.username}'
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n📧 Email Verification Summary:'
                f'\n   Newly Verified: {verified_count}'
            )
        )

    def display_summary(self):
        """Display current verification and location summary"""
        self.stdout.write('\n📊 CURRENT STATUS SUMMARY:')
        self.stdout.write('-' * 40)
        
        # Verification statistics
        total_profiles = Profile.objects.count()
        verified_profiles = Profile.objects.filter(email_verified=True).count()
        unverified_profiles = Profile.objects.filter(email_verified=False).count()
        
        self.stdout.write(f'👥 Total Users: {total_profiles}')
        self.stdout.write(f'✅ Verified Users: {verified_profiles}')
        self.stdout.write(f'❌ Unverified Users: {unverified_profiles}')
        self.stdout.write(f'📈 Verification Rate: {(verified_profiles/total_profiles*100):.1f}%')
        
        # Location statistics
        profiles_with_location = Profile.objects.exclude(country__isnull=True).exclude(country='').count()
        self.stdout.write(f'🌍 Users with Location: {profiles_with_location}')
        self.stdout.write(f'📍 Location Coverage: {(profiles_with_location/total_profiles*100):.1f}%')
        
        # Geographic distribution
        from collections import Counter
        countries = Profile.objects.exclude(country__isnull=True).exclude(country='').values_list('country', flat=True)
        country_counts = Counter(countries)
        
        if country_counts:
            self.stdout.write('\n🌍 Geographic Distribution:')
            for country, count in country_counts.most_common():
                self.stdout.write(f'   {country}: {count} users')
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎉 Admin interface is now ready with enhanced verification and location display!'
            )
        )
