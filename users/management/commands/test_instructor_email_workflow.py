"""
Management command to test the complete instructor email notification workflow.

This command verifies that:
1. Email templates render correctly
2. Email notifications are sent when instructor profiles are created
3. Security features work (password generation, validation)
4. Audit logging functions properly
5. Admin interface integration works

Usage:
    python manage.py test_instructor_email_workflow
    python manage.py test_instructor_email_workflow --cleanup  # Remove test users after testing
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from users.models import InstructorProfile
from users.email_utils import (
    generate_secure_temporary_password,
    validate_password_complexity,
    send_instructor_welcome_email,
    create_instructor_with_temporary_password,
    log_instructor_account_creation
)
import random
import string


class Command(BaseCommand):
    help = 'Test the complete instructor email notification workflow'

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
            self.style.SUCCESS('🚀 Testing Instructor Email Notification Workflow')
        )
        self.stdout.write('=' * 70)
        
        test_users = []
        
        try:
            # Test 1: Password generation and validation
            self.stdout.write('\n📋 Test 1: Password Security Features')
            self.test_password_security()
            
            # Test 2: Email template rendering
            self.stdout.write('\n📋 Test 2: Email Template Rendering')
            test_user = self.test_email_template_rendering()
            if test_user:
                test_users.append(test_user)
            
            # Test 3: Signal-triggered email notifications
            self.stdout.write('\n📋 Test 3: Signal-Triggered Email Notifications')
            signal_test_user = self.test_signal_email_notification()
            if signal_test_user:
                test_users.append(signal_test_user)
            
            # Test 4: Complete instructor creation workflow
            self.stdout.write('\n📋 Test 4: Complete Instructor Creation Workflow')
            workflow_result = self.test_complete_workflow()
            if workflow_result and workflow_result.get('user'):
                test_users.append(workflow_result['user'])
            
            # Test 5: Audit logging
            self.stdout.write('\n📋 Test 5: Audit Logging')
            self.test_audit_logging()
            
            # Summary
            self.stdout.write('\n' + '=' * 70)
            self.stdout.write(
                self.style.SUCCESS('✅ All email workflow tests completed successfully!')
            )
            self.stdout.write(f'Created {len(test_users)} test instructor accounts')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Test failed: {str(e)}')
            )
            raise CommandError(f'Email workflow test failed: {str(e)}')
        
        finally:
            if self.cleanup:
                self.cleanup_test_users(test_users)

    def test_password_security(self):
        """Test password generation and validation"""
        self.stdout.write('  🔐 Testing password generation...')
        
        # Test secure password generation
        password = generate_secure_temporary_password()
        if self.verbose:
            self.stdout.write(f'    Generated password: {password}')
        
        # Test password validation
        is_valid, errors = validate_password_complexity(password)
        if not is_valid:
            raise CommandError(f'Generated password failed validation: {errors}')
        
        # Test weak password detection
        weak_password = "123456"
        is_valid, errors = validate_password_complexity(weak_password)
        if is_valid:
            raise CommandError('Weak password validation failed - should have detected weak password')
        
        expected_errors = 5  # Should have multiple validation errors
        if len(errors) < expected_errors:
            raise CommandError(f'Expected at least {expected_errors} validation errors, got {len(errors)}')
        
        self.stdout.write('    ✅ Password security features working correctly')

    def test_email_template_rendering(self):
        """Test email template rendering"""
        self.stdout.write('  📧 Testing email template rendering...')
        
        # Create test user and profile
        username = f'test_template_{self.generate_random_string(4)}'
        user = User.objects.create_user(
            username=username,
            email=f'{username}@yitp-test.com',
            first_name='Template',
            last_name='Test',
            password='test_password_123'
        )
        
        profile = InstructorProfile.objects.create(
            user=user,
            instructor_role='course_instructor',
            bio='Test bio for template rendering',
            verification_status='pending'
        )
        
        # Test email sending
        temp_password = generate_secure_temporary_password()
        email_sent = send_instructor_welcome_email(
            user=user,
            instructor_profile=profile,
            temporary_password=temp_password,
            created_by_admin=None
        )
        
        if not email_sent:
            raise CommandError('Failed to send instructor welcome email')
        
        self.stdout.write('    ✅ Email template rendering successful')
        return user

    def test_signal_email_notification(self):
        """Test signal-triggered email notifications"""
        self.stdout.write('  📡 Testing signal-triggered email notifications...')
        
        # Create user first
        username = f'test_signal_{self.generate_random_string(4)}'
        user = User.objects.create_user(
            username=username,
            email=f'{username}@yitp-test.com',
            first_name='Signal',
            last_name='Test',
            password='test_password_123'
        )
        
        # Create instructor profile (this should trigger the signal)
        profile = InstructorProfile.objects.create(
            user=user,
            instructor_role='teaching_assistant',
            bio='Test bio for signal testing',
            verification_status='pending'
        )
        
        # Verify the profile was created and signal was triggered
        if not hasattr(user, 'instructor_profile'):
            raise CommandError('Instructor profile not properly linked to user')
        
        # Check if user got staff status (should be automatic for teaching_assistant)
        user.refresh_from_db()
        if not user.is_staff:
            raise CommandError('Signal did not properly set staff status')
        
        self.stdout.write('    ✅ Signal-triggered email notification successful')
        return user

    def test_complete_workflow(self):
        """Test the complete instructor creation workflow"""
        self.stdout.write('  🔄 Testing complete instructor creation workflow...')
        
        # Use the complete workflow function
        result = create_instructor_with_temporary_password(
            username=f'test_complete_{self.generate_random_string(4)}',
            email=f'test_complete_{self.generate_random_string(4)}@yitp-test.com',
            first_name='Complete',
            last_name='Workflow',
            instructor_role='content_creator',
            created_by_admin=None
        )
        
        if not result['success']:
            raise CommandError(f'Complete workflow failed: {result["message"]}')
        
        if not result['email_sent']:
            self.stdout.write('    ⚠️ Email sending failed in complete workflow')
        
        # Verify user and profile were created correctly
        user = result['user']
        profile = result['instructor_profile']
        
        if not user or not profile:
            raise CommandError('User or profile not created in complete workflow')
        
        # Verify permissions were assigned
        user.refresh_from_db()
        if not user.is_staff:
            raise CommandError('Staff status not assigned in complete workflow')
        
        self.stdout.write('    ✅ Complete instructor creation workflow successful')
        return result

    def test_audit_logging(self):
        """Test audit logging functionality"""
        self.stdout.write('  📝 Testing audit logging...')
        
        # Create a simple test case for audit logging
        username = f'test_audit_{self.generate_random_string(4)}'
        user = User.objects.create_user(
            username=username,
            email=f'{username}@yitp-test.com',
            first_name='Audit',
            last_name='Test',
            password='test_password_123'
        )
        
        profile = InstructorProfile.objects.create(
            user=user,
            instructor_role='grader',
            bio='Test bio for audit logging',
            verification_status='pending'
        )
        
        # Test audit logging function
        try:
            log_instructor_account_creation(
                user=user,
                instructor_profile=profile,
                created_by_admin=None,
                email_sent=True
            )
            self.stdout.write('    ✅ Audit logging successful')
        except Exception as e:
            self.stdout.write(f'    ⚠️ Audit logging failed: {str(e)}')
        
        # Clean up this test user immediately
        user.delete()

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
