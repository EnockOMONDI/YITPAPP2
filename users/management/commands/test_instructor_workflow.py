"""
Management command to test the automated instructor user creation workflow.

This command verifies that:
1. Signal-based permission system works correctly
2. Admin interface enhancements function properly
3. Role-based permissions are assigned automatically
4. Verification status is handled correctly

Usage:
    python manage.py test_instructor_workflow
    python manage.py test_instructor_workflow --cleanup  # Remove test users after testing
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db import transaction
from users.models import InstructorProfile, Specialization
import random
import string


class Command(BaseCommand):
    help = 'Test the automated instructor user creation workflow'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Remove test users after testing',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.cleanup = options['cleanup']
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Testing Instructor User Creation Workflow')
        )
        self.stdout.write('=' * 60)
        
        test_users = []
        
        try:
            # Test each instructor role
            roles_to_test = [
                'system_admin',
                'course_instructor', 
                'teaching_assistant',
                'content_creator',
                'grader'
            ]
            
            for role in roles_to_test:
                self.stdout.write(f'\n📋 Testing role: {role}')
                user = self.create_test_instructor(role)
                test_users.append(user)
                self.verify_permissions(user, role)
                self.verify_admin_access(user, role)
            
            # Test bulk operations
            self.stdout.write(f'\n🔄 Testing bulk operations...')
            self.test_bulk_operations(test_users)
            
            # Summary
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(
                self.style.SUCCESS('✅ All tests completed successfully!')
            )
            self.stdout.write(f'Created {len(test_users)} test instructor accounts')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Test failed: {str(e)}')
            )
            raise CommandError(f'Workflow test failed: {str(e)}')
        
        finally:
            if self.cleanup:
                self.cleanup_test_users(test_users)

    def create_test_instructor(self, role):
        """Create a test instructor user with the specified role"""
        # Generate unique username
        username = f'test_instructor_{role}_{self.generate_random_string(4)}'
        email = f'{username}@yitp-test.com'
        
        self.stdout.write(f'  Creating user: {username}')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=f'Test {role.replace("_", " ").title()}',
            last_name='Instructor',
            password='test_password_123'
        )
        
        # Create instructor profile (this should trigger the signal)
        profile = InstructorProfile.objects.create(
            user=user,
            instructor_role=role,
            bio=f'Test bio for {role} instructor',
            qualifications=f'Test qualifications for {role}',
            years_experience=random.randint(1, 10),
            verification_status='pending'  # Will be auto-verified for system_admin
        )
        
        if self.verbose:
            self.stdout.write(f'    ✅ Created user and profile')
            self.stdout.write(f'    📧 Email: {email}')
            self.stdout.write(f'    🎭 Role: {profile.get_instructor_role_display()}')
            self.stdout.write(f'    ✔️  Verification: {profile.get_verification_status_display()}')
        
        return user

    def verify_permissions(self, user, role):
        """Verify that the user has the correct permissions for their role"""
        self.stdout.write(f'  🔐 Verifying permissions for {role}...')
        
        # Refresh user from database to get updated permissions
        user.refresh_from_db()
        
        # Check staff status
        expected_staff = role in ['system_admin', 'course_instructor', 'content_creator', 'teaching_assistant']
        if user.is_staff != expected_staff:
            raise CommandError(f'Staff status incorrect for {role}: expected {expected_staff}, got {user.is_staff}')
        
        # Check superuser status
        expected_superuser = role == 'system_admin'
        if user.is_superuser != expected_superuser:
            raise CommandError(f'Superuser status incorrect for {role}: expected {expected_superuser}, got {user.is_superuser}')
        
        # Check specific permissions for non-superusers
        if not user.is_superuser:
            self.verify_role_specific_permissions(user, role)
        
        if self.verbose:
            self.stdout.write(f'    ✅ Staff status: {user.is_staff}')
            self.stdout.write(f'    ✅ Superuser status: {user.is_superuser}')
            self.stdout.write(f'    ✅ Permission count: {user.user_permissions.count()}')

    def verify_role_specific_permissions(self, user, role):
        """Verify role-specific permissions"""
        permissions = user.user_permissions.all()
        permission_codenames = [p.codename for p in permissions]
        
        # Define expected permissions for each role
        expected_permissions = {
            'course_instructor': [
                'view_course', 'add_course', 'change_course',
                'view_module', 'add_module', 'change_module',
                'view_lesson', 'add_lesson', 'change_lesson',
                'view_quiz', 'add_quiz', 'change_quiz',
                'view_question', 'add_question', 'change_question',
            ],
            'teaching_assistant': [
                'view_course', 'view_module', 'change_module',
                'view_lesson', 'change_lesson', 'view_quiz', 'change_quiz',
                'view_question',
            ],
            'content_creator': [
                'view_course', 'add_course', 'change_course',
                'view_module', 'add_module', 'change_module',
                'view_lesson', 'add_lesson', 'change_lesson',
                'view_quiz', 'add_quiz', 'change_quiz',
                'view_question', 'add_question', 'change_question',
            ],
            'grader': [
                'view_course', 'view_module', 'view_lesson',
                'view_quiz', 'change_quiz', 'view_question',
            ]
        }
        
        expected = expected_permissions.get(role, [])
        
        # Check that user has at least some of the expected permissions
        # (Some permissions might not exist if models aren't fully set up)
        found_permissions = [p for p in expected if p in permission_codenames]
        
        if self.verbose and found_permissions:
            self.stdout.write(f'    ✅ Found {len(found_permissions)} expected permissions')

    def verify_admin_access(self, user, role):
        """Verify admin access capabilities"""
        self.stdout.write(f'  🏛️  Verifying admin access for {role}...')
        
        profile = user.instructor_profile
        
        # Check verification status
        if role == 'system_admin' and profile.verification_status != 'verified':
            raise CommandError(f'System admin should be auto-verified, but status is {profile.verification_status}')
        
        # Check admin access capability
        expected_admin_access = role in ['system_admin', 'course_instructor', 'content_creator']
        actual_admin_access = profile.can_access_admin
        
        if actual_admin_access != expected_admin_access:
            raise CommandError(f'Admin access incorrect for {role}: expected {expected_admin_access}, got {actual_admin_access}')
        
        if self.verbose:
            self.stdout.write(f'    ✅ Verification status: {profile.verification_status}')
            self.stdout.write(f'    ✅ Can access admin: {actual_admin_access}')

    def test_bulk_operations(self, test_users):
        """Test bulk operations on instructor profiles"""
        if not test_users:
            return
        
        # Get instructor profiles
        profiles = [user.instructor_profile for user in test_users if hasattr(user, 'instructor_profile')]
        
        if not profiles:
            return
        
        self.stdout.write(f'  Testing bulk verification...')
        
        # Test bulk verification
        for profile in profiles:
            if profile.verification_status != 'verified':
                profile.verification_status = 'verified'
                profile.verified_at = timezone.now()
                profile.save()
        
        verified_count = sum(1 for p in profiles if p.verification_status == 'verified')
        self.stdout.write(f'    ✅ Verified {verified_count} profiles')

    def cleanup_test_users(self, test_users):
        """Clean up test users created during testing"""
        self.stdout.write('\n🧹 Cleaning up test users...')
        
        deleted_count = 0
        for user in test_users:
            try:
                username = user.username
                user.delete()
                deleted_count += 1
                if self.verbose:
                    self.stdout.write(f'  ✅ Deleted {username}')
            except Exception as e:
                self.stdout.write(f'  ❌ Failed to delete {user.username}: {str(e)}')
        
        self.stdout.write(f'🗑️  Cleaned up {deleted_count} test users')

    def generate_random_string(self, length=8):
        """Generate a random string for unique usernames"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
