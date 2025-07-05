#!/usr/bin/env python3
"""
YITP User Registration Journey Test Suite
=========================================

Comprehensive test suite for the complete YITP user registration workflow
from initial form submission through OTP verification to account activation.

Test Coverage:
1. Registration Form Validation & Submission
2. User Account Creation & Database State
3. OTP Generation, Storage & Email Delivery
4. OTP Verification Process (Valid, Invalid, Expired)
5. Automatic User Login After Verification
6. Profile Creation & Email Verification Status
7. Session Management & Welcome Page Redirection
8. Email Notifications (OTP, Welcome, Admin)
9. Error Handling & Edge Cases
10. Middleware Integration & Smart Redirects

Author: YITP Development Team
Date: 2025-01-05
"""

import os
import sys
import django
import unittest
import logging
from datetime import datetime, timedelta

# Setup Django environment BEFORE importing Django modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

# Now import Django modules
from django.utils import timezone
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.sessions.models import Session
from django.conf import settings

from users.models import OTPVerification, Profile
from users.otp_views import generate_and_send_otp, send_otp_for_registration
from users.email_utils import send_otp_email, send_welcome_email, send_otp_verification_admin_notification
from yitp.middleware import WelcomePageRedirectMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tests/test_user_registration_journey.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class UserRegistrationJourneyTestCase(TestCase):
    """Base test case with common setup and utilities"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.test_user_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'testuser',
            'email': 'testuser@example.com',
            'phone_number': '+1234567890',
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
            'terms': 'on'
        }
        self.test_results = []
        
        # Clear any existing test data
        User.objects.filter(username__startswith='test').delete()
        OTPVerification.objects.all().delete()
        Profile.objects.filter(user__username__startswith='test').delete()
        
        # Clear email outbox
        mail.outbox = []
        
        logger.info("=" * 60)
        logger.info(f"🧪 Starting test: {self._testMethodName}")
        logger.info("=" * 60)
    
    def tearDown(self):
        """Clean up after test"""
        # Clean up test data
        User.objects.filter(username__startswith='test').delete()
        OTPVerification.objects.all().delete()
        Profile.objects.filter(user__username__startswith='test').delete()
        
        logger.info(f"✅ Completed test: {self._testMethodName}")
        logger.info("-" * 60)
    
    def log_test_result(self, test_name, success, message, details=""):
        """Log test result with consistent formatting"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        if details:
            logger.info(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        })
        
        return success
    
    def create_test_user(self, username_suffix="", email_suffix=""):
        """Create a test user with optional suffix"""
        username = f"testuser{username_suffix}"
        email = f"testuser{email_suffix}@example.com"
        
        user_data = self.test_user_data.copy()
        user_data['username'] = username
        user_data['email'] = email
        
        return user_data
    
    def submit_registration_form(self, user_data=None):
        """Submit registration form and return response"""
        if user_data is None:
            user_data = self.test_user_data
        
        response = self.client.post('/register/', user_data, follow=True)
        return response
    
    def get_latest_otp_for_user(self, user):
        """Get the latest OTP record for a user"""
        return OTPVerification.objects.filter(user=user).order_by('-created_at').first()


class RegistrationFormValidationTests(UserRegistrationJourneyTestCase):
    """Test registration form validation and submission"""
    
    def test_registration_form_access(self):
        """Test that registration form is accessible"""
        response = self.client.get('/register/')
        
        success = response.status_code == 200
        message = f"Registration form accessible (Status: {response.status_code})"
        
        self.log_test_result("Registration Form Access", success, message)
        self.assertEqual(response.status_code, 200)
    
    def test_valid_registration_submission(self):
        """Test successful registration with valid data"""
        initial_user_count = User.objects.count()
        
        response = self.submit_registration_form()
        
        # Check if user was created
        final_user_count = User.objects.count()
        user_created = final_user_count == initial_user_count + 1
        
        # Check if redirected to OTP verification
        redirected_to_otp = '/verify-otp/' in response.redirect_chain[-1][0] if response.redirect_chain else False
        
        success = user_created and redirected_to_otp
        message = f"User created: {user_created}, Redirected to OTP: {redirected_to_otp}"
        
        self.log_test_result("Valid Registration Submission", success, message)
        self.assertTrue(success)
    
    def test_duplicate_username_validation(self):
        """Test validation for duplicate username"""
        # Create first user
        User.objects.create_user(
            username=self.test_user_data['username'],
            email='different@example.com',
            password='password123'
        )
        
        response = self.submit_registration_form()
        
        # Check that form was not submitted successfully
        success = response.status_code == 200 and 'Username already taken' in str(response.content)
        message = "Duplicate username properly rejected"
        
        self.log_test_result("Duplicate Username Validation", success, message)
        self.assertTrue(success)
    
    def test_duplicate_email_validation(self):
        """Test validation for duplicate email"""
        # Create first user
        User.objects.create_user(
            username='differentuser',
            email=self.test_user_data['email'],
            password='password123'
        )
        
        response = self.submit_registration_form()
        
        # Check that form was not submitted successfully
        success = response.status_code == 200 and 'Email already registered' in str(response.content)
        message = "Duplicate email properly rejected"
        
        self.log_test_result("Duplicate Email Validation", success, message)
        self.assertTrue(success)
    
    def test_password_mismatch_validation(self):
        """Test validation for password mismatch"""
        user_data = self.test_user_data.copy()
        user_data['password2'] = 'DifferentPassword123!'
        
        response = self.submit_registration_form(user_data)
        
        # Check that form was not submitted successfully
        success = response.status_code == 200 and 'Passwords do not match' in str(response.content)
        message = "Password mismatch properly rejected"
        
        self.log_test_result("Password Mismatch Validation", success, message)
        self.assertTrue(success)
    
    def test_required_fields_validation(self):
        """Test validation for required fields"""
        user_data = self.test_user_data.copy()
        user_data['first_name'] = ''  # Remove required field
        
        response = self.submit_registration_form(user_data)
        
        # Check that form was not submitted successfully
        success = response.status_code == 200 and 'All fields are required' in str(response.content)
        message = "Missing required fields properly rejected"
        
        self.log_test_result("Required Fields Validation", success, message)
        self.assertTrue(success)


class UserAccountCreationTests(UserRegistrationJourneyTestCase):
    """Test user account creation and database state"""
    
    def test_user_creation_with_correct_data(self):
        """Test that user is created with correct data"""
        response = self.submit_registration_form()
        
        # Get created user
        user = User.objects.filter(username=self.test_user_data['username']).first()
        
        if user:
            # Verify user data
            data_correct = (
                user.first_name == self.test_user_data['first_name'] and
                user.last_name == self.test_user_data['last_name'] and
                user.email == self.test_user_data['email'] and
                not user.is_active  # Should be inactive until OTP verification
            )
            
            success = data_correct
            message = f"User created with correct data, inactive status: {not user.is_active}"
        else:
            success = False
            message = "User was not created"
        
        self.log_test_result("User Creation with Correct Data", success, message)
        self.assertTrue(success)
    
    def test_profile_creation_during_registration(self):
        """Test that user profile is created during registration"""
        response = self.submit_registration_form()
        
        user = User.objects.filter(username=self.test_user_data['username']).first()
        
        if user:
            try:
                profile = user.profile
                phone_correct = profile.phone_number == self.test_user_data['phone_number']
                
                success = phone_correct
                message = f"Profile created with phone: {profile.phone_number}"
            except Profile.DoesNotExist:
                success = False
                message = "Profile was not created"
        else:
            success = False
            message = "User was not created"
        
        self.log_test_result("Profile Creation During Registration", success, message)
        self.assertTrue(success)


class OTPGenerationAndEmailTests(UserRegistrationJourneyTestCase):
    """Test OTP generation, storage, and email delivery"""

    def test_otp_generation_and_storage(self):
        """Test that OTP is generated and stored correctly"""
        response = self.submit_registration_form()

        user = User.objects.filter(username=self.test_user_data['username']).first()

        if user:
            otp_record = self.get_latest_otp_for_user(user)

            if otp_record:
                # Verify OTP properties
                otp_valid = (
                    len(otp_record.otp_code) == 6 and
                    otp_record.otp_code.isdigit() and
                    not otp_record.is_used and
                    not otp_record.is_verified and
                    otp_record.expires_at > timezone.now()
                )

                success = otp_valid
                message = f"OTP generated: {otp_record.otp_code}, expires: {otp_record.expires_at}"
            else:
                success = False
                message = "OTP record was not created"
        else:
            success = False
            message = "User was not created"

        self.log_test_result("OTP Generation and Storage", success, message)
        self.assertTrue(success)

    def test_otp_email_delivery(self):
        """Test that OTP email is sent correctly"""
        mail.outbox = []  # Clear email outbox

        response = self.submit_registration_form()

        # Check if email was sent
        email_sent = len(mail.outbox) > 0

        if email_sent:
            email = mail.outbox[0]
            user = User.objects.filter(username=self.test_user_data['username']).first()
            otp_record = self.get_latest_otp_for_user(user) if user else None

            # Verify email content
            email_correct = (
                email.to[0] == self.test_user_data['email'] and
                'YITP Verification Code' in email.subject and
                otp_record and otp_record.otp_code in email.body
            )

            success = email_correct
            message = f"Email sent to {email.to[0]}, subject: {email.subject}"
        else:
            success = False
            message = "No email was sent"

        self.log_test_result("OTP Email Delivery", success, message)
        self.assertTrue(success)

    def test_multiple_otp_invalidation(self):
        """Test that previous OTPs are invalidated when new one is generated"""
        # Create user and generate first OTP
        user = User.objects.create_user(
            username='multipleotpuser',
            email='multipleotpuser@example.com',
            password='password123'
        )

        # Generate first OTP
        otp1, email_sent1 = generate_and_send_otp(user)

        # Generate second OTP
        otp2, email_sent2 = generate_and_send_otp(user)

        # Refresh first OTP from database
        otp1.refresh_from_db()

        # Check that first OTP is invalidated
        success = otp1.is_used and not otp2.is_used
        message = f"First OTP invalidated: {otp1.is_used}, Second OTP valid: {not otp2.is_used}"

        self.log_test_result("Multiple OTP Invalidation", success, message)
        self.assertTrue(success)


class OTPVerificationTests(UserRegistrationJourneyTestCase):
    """Test OTP verification process"""

    def test_valid_otp_verification(self):
        """Test successful OTP verification"""
        # Register user
        response = self.submit_registration_form()
        user = User.objects.filter(username=self.test_user_data['username']).first()
        otp_record = self.get_latest_otp_for_user(user)

        # Verify OTP
        verification_response = self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': otp_record.otp_code
        }, follow=True)

        # Check results
        user.refresh_from_db()
        otp_record.refresh_from_db()

        # Verify user is activated and logged in
        user_activated = user.is_active
        otp_used = otp_record.is_used and otp_record.is_verified
        redirected_to_welcome = '/welcome/' in verification_response.redirect_chain[-1][0] if verification_response.redirect_chain else False

        success = user_activated and otp_used and redirected_to_welcome
        message = f"User activated: {user_activated}, OTP used: {otp_used}, Redirected to welcome: {redirected_to_welcome}"

        self.log_test_result("Valid OTP Verification", success, message)
        self.assertTrue(success)

    def test_invalid_otp_verification(self):
        """Test verification with invalid OTP"""
        # Register user
        response = self.submit_registration_form()
        user = User.objects.filter(username=self.test_user_data['username']).first()

        # Try to verify with invalid OTP
        verification_response = self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': '000000'  # Invalid OTP
        })

        # Check that verification failed
        user.refresh_from_db()

        success = not user.is_active and 'Invalid or expired OTP' in str(verification_response.content)
        message = f"User remains inactive: {not user.is_active}, Error message shown"

        self.log_test_result("Invalid OTP Verification", success, message)
        self.assertTrue(success)

    def test_expired_otp_verification(self):
        """Test verification with expired OTP"""
        # Create user and OTP
        user = User.objects.create_user(
            username='expiredotpuser',
            email='expiredotpuser@example.com',
            password='password123',
            is_active=False
        )

        # Create expired OTP
        expired_otp = OTPVerification.objects.create(
            user=user,
            otp_code='123456',
            expires_at=timezone.now() - timedelta(minutes=1)  # Expired
        )

        # Try to verify with expired OTP
        verification_response = self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': expired_otp.otp_code
        })

        # Check that verification failed
        user.refresh_from_db()

        success = not user.is_active and 'Invalid or expired OTP' in str(verification_response.content)
        message = f"User remains inactive: {not user.is_active}, Expired OTP rejected"

        self.log_test_result("Expired OTP Verification", success, message)
        self.assertTrue(success)


class PostVerificationWorkflowTests(UserRegistrationJourneyTestCase):
    """Test post-OTP verification workflow"""

    def test_automatic_login_after_verification(self):
        """Test that user is automatically logged in after OTP verification"""
        # Register and verify user
        response = self.submit_registration_form()
        user = User.objects.filter(username=self.test_user_data['username']).first()
        otp_record = self.get_latest_otp_for_user(user)

        verification_response = self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': otp_record.otp_code
        }, follow=True)

        # Check if user is logged in
        user_logged_in = verification_response.wsgi_request.user.is_authenticated
        correct_user = verification_response.wsgi_request.user.id == user.id

        success = user_logged_in and correct_user
        message = f"User logged in: {user_logged_in}, Correct user: {correct_user}"

        self.log_test_result("Automatic Login After Verification", success, message)
        self.assertTrue(success)

    def test_profile_email_verification_status(self):
        """Test that profile email verification status is updated"""
        # Register and verify user
        response = self.submit_registration_form()
        user = User.objects.filter(username=self.test_user_data['username']).first()
        otp_record = self.get_latest_otp_for_user(user)

        verification_response = self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': otp_record.otp_code
        })

        # Check profile email verification status
        user.refresh_from_db()
        profile = user.profile

        success = profile.email_verified
        message = f"Email verification status: {profile.email_verified}"

        self.log_test_result("Profile Email Verification Status", success, message)
        self.assertTrue(success)

    def test_session_flag_management(self):
        """Test that session flags are set correctly for welcome page"""
        # Register and verify user
        response = self.submit_registration_form()
        user = User.objects.filter(username=self.test_user_data['username']).first()
        otp_record = self.get_latest_otp_for_user(user)

        verification_response = self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': otp_record.otp_code
        })

        # Check session flags
        session = self.client.session
        otp_flag_set = session.get('just_completed_otp_verification', False)
        timestamp_set = 'otp_verification_timestamp' in session

        success = otp_flag_set and timestamp_set
        message = f"OTP flag set: {otp_flag_set}, Timestamp set: {timestamp_set}"

        self.log_test_result("Session Flag Management", success, message)
        self.assertTrue(success)


class EmailNotificationTests(UserRegistrationJourneyTestCase):
    """Test email notification system"""

    def test_welcome_email_after_verification(self):
        """Test that welcome email is sent after successful verification"""
        mail.outbox = []  # Clear email outbox

        # Register and verify user
        self.submit_registration_form()
        user = User.objects.filter(username=self.test_user_data['username']).first()
        otp_record = self.get_latest_otp_for_user(user)

        # Clear outbox after registration (OTP email)
        mail.outbox = []

        # Verify OTP
        self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': otp_record.otp_code
        })

        # Check if welcome email was sent
        welcome_email_sent = any('Welcome to YITP' in email.subject for email in mail.outbox)

        success = welcome_email_sent
        message = f"Welcome email sent: {welcome_email_sent}"

        self.log_test_result("Welcome Email After Verification", success, message)
        self.assertTrue(success)

    def test_admin_notification_email(self):
        """Test that admin notification is sent after verification"""
        mail.outbox = []  # Clear email outbox

        # Register and verify user
        self.submit_registration_form()
        user = User.objects.filter(username=self.test_user_data['username']).first()
        otp_record = self.get_latest_otp_for_user(user)

        # Clear outbox after registration
        mail.outbox = []

        # Verify OTP
        self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': otp_record.otp_code
        })

        # Check if admin notification was sent
        admin_email_sent = any('New User Verified' in email.subject for email in mail.outbox)

        success = admin_email_sent
        message = f"Admin notification sent: {admin_email_sent}"

        self.log_test_result("Admin Notification Email", success, message)
        self.assertTrue(success)


class MiddlewareIntegrationTests(UserRegistrationJourneyTestCase):
    """Test middleware integration and smart redirects"""

    def test_welcome_page_redirect_with_session_flag(self):
        """Test that welcome page is accessible with session flag"""
        # Register and verify user
        self.submit_registration_form()
        user = User.objects.filter(username=self.test_user_data['username']).first()
        otp_record = self.get_latest_otp_for_user(user)

        # Verify OTP (this should set session flag and redirect to welcome)
        verification_response = self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': otp_record.otp_code
        }, follow=True)

        # Check if redirected to welcome page
        final_url = verification_response.redirect_chain[-1][0] if verification_response.redirect_chain else ''
        redirected_to_welcome = '/welcome/' in final_url

        success = redirected_to_welcome
        message = f"Redirected to welcome page: {redirected_to_welcome}"

        self.log_test_result("Welcome Page Redirect with Session Flag", success, message)
        self.assertTrue(success)

    def test_authenticated_user_redirect_from_registration(self):
        """Test that authenticated users are redirected away from registration"""
        # Create and login user
        user = User.objects.create_user(
            username='authenticateduser',
            email='authenticated@example.com',
            password='password123',
            is_active=True
        )
        self.client.force_login(user)

        # Try to access registration page
        response = self.client.get('/register/')

        # Should be redirected away from registration
        success = response.status_code == 302
        message = f"Authenticated user redirected from registration (Status: {response.status_code})"

        self.log_test_result("Authenticated User Redirect from Registration", success, message)
        self.assertTrue(success)


class ErrorHandlingTests(UserRegistrationJourneyTestCase):
    """Test error handling and edge cases"""

    def test_registration_with_email_failure(self):
        """Test registration when email sending fails"""
        # Mock email failure by temporarily changing email settings
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.dummy.EmailBackend'):
            response = self.submit_registration_form()

            user = User.objects.filter(username=self.test_user_data['username']).first()

            # User should still be created and activated as fallback
            success = user and user.is_active
            message = f"User created and activated despite email failure: {success}"

            self.log_test_result("Registration with Email Failure", success, message)
            self.assertTrue(success)

    def test_otp_verification_with_missing_user_id(self):
        """Test OTP verification with missing user ID"""
        response = self.client.post('/verify-otp/', {
            'otp_code': '123456'
            # Missing user_id
        })

        # Should show error message
        success = 'Please provide both user ID and OTP code' in str(response.content)
        message = "Missing user ID properly handled"

        self.log_test_result("OTP Verification with Missing User ID", success, message)
        self.assertTrue(success)

    def test_otp_verification_with_invalid_user_id(self):
        """Test OTP verification with invalid user ID"""
        response = self.client.post('/verify-otp/', {
            'user_id': '99999',  # Non-existent user ID
            'otp_code': '123456'
        })

        # Should show error message
        success = 'Invalid user' in str(response.content)
        message = "Invalid user ID properly handled"

        self.log_test_result("OTP Verification with Invalid User ID", success, message)
        self.assertTrue(success)


class ProfileCompletionTests(UserRegistrationJourneyTestCase):
    """Test profile completion tracking"""

    def test_profile_completion_calculation(self):
        """Test that profile completion percentage is calculated correctly"""
        # Register and verify user
        self.submit_registration_form()
        user = User.objects.filter(username=self.test_user_data['username']).first()
        otp_record = self.get_latest_otp_for_user(user)

        # Verify OTP
        self.client.post('/verify-otp/', {
            'user_id': user.id,
            'otp_code': otp_record.otp_code
        })

        # Check profile completion
        user.refresh_from_db()
        profile = user.profile
        completion_percentage = profile.profile_completion_percentage

        # Should have some completion due to basic fields being filled
        success = completion_percentage > 0
        message = f"Profile completion calculated: {completion_percentage}%"

        self.log_test_result("Profile Completion Calculation", success, message)
        self.assertTrue(success)


class ComprehensiveWorkflowTest(UserRegistrationJourneyTestCase):
    """Comprehensive end-to-end workflow test"""

    def test_complete_registration_journey(self):
        """Test the complete registration journey from start to finish"""
        mail.outbox = []  # Clear email outbox

        # Step 1: Submit registration form
        response = self.submit_registration_form()
        step1_success = response.status_code == 302 and '/verify-otp/' in response.url

        # Step 2: Verify user and OTP creation
        user = User.objects.filter(username=self.test_user_data['username']).first()
        otp_record = self.get_latest_otp_for_user(user) if user else None
        step2_success = user and otp_record and not user.is_active

        # Step 3: Verify OTP email was sent
        step3_success = len(mail.outbox) > 0 and any('YITP Verification Code' in email.subject for email in mail.outbox)

        # Step 4: Verify OTP
        if otp_record:
            verification_response = self.client.post('/verify-otp/', {
                'user_id': user.id,
                'otp_code': otp_record.otp_code
            }, follow=True)
            step4_success = verification_response.status_code == 200
        else:
            step4_success = False

        # Step 5: Verify user activation and login
        if user:
            user.refresh_from_db()
            step5_success = user.is_active and user.profile.email_verified
        else:
            step5_success = False

        # Step 6: Verify welcome page redirect
        step6_success = '/welcome/' in verification_response.redirect_chain[-1][0] if verification_response.redirect_chain else False

        # Overall success
        all_steps_success = all([step1_success, step2_success, step3_success, step4_success, step5_success, step6_success])

        message = f"Steps: Registration({step1_success}), User/OTP({step2_success}), Email({step3_success}), Verification({step4_success}), Activation({step5_success}), Redirect({step6_success})"

        self.log_test_result("Complete Registration Journey", all_steps_success, message)
        self.assertTrue(all_steps_success)


def run_test_suite():
    """Run the complete test suite and generate summary report"""
    print("\n" + "=" * 80)
    print("🚀 YITP USER REGISTRATION JOURNEY TEST SUITE")
    print("=" * 80)

    # Create test suite
    test_classes = [
        RegistrationFormValidationTests,
        UserAccountCreationTests,
        OTPGenerationAndEmailTests,
        OTPVerificationTests,
        PostVerificationWorkflowTests,
        EmailNotificationTests,
        MiddlewareIntegrationTests,
        ErrorHandlingTests,
        ProfileCompletionTests,
        ComprehensiveWorkflowTest
    ]

    suite = unittest.TestSuite()
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY REPORT")
    print("=" * 80)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")

    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip() if 'AssertionError:' in traceback else 'Unknown failure'}")

    if result.errors:
        print("\n🚨 ERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip() if 'Exception:' in traceback else 'Unknown error'}")

    print("\n" + "=" * 80)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_test_suite()
    sys.exit(0 if success else 1)
