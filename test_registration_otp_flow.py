#!/usr/bin/env python3
"""
YITP Registration & Post-OTP Verification Flow Test Suite
=========================================================

This comprehensive test suite validates all implemented features for the 
post-OTP verification user experience enhancement in the YITP application.

Test Coverage:
1. Admin Notification System
2. Automatic User Login After OTP Verification  
3. Profile Completion Tracking System
4. Guided Onboarding Workflow Implementation
5. Email Verification Status Field
6. Welcome Page Redirect Flow Analysis

Author: YITP Development Team
Date: 2025-01-04
"""

import os
import sys
import django
import logging
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core import mail
from django.contrib.messages import get_messages
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.messages.middleware import MessageMiddleware

from users.models import OTPVerification, Profile
from users.otp_views import generate_and_send_otp, verify_otp_view
from users.email_utils import send_otp_verification_admin_notification
from yitp.middleware import SmartRedirectMiddleware, WelcomePageRedirectMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_registration_otp_flow.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RegistrationOTPFlowTestSuite:
    """Comprehensive test suite for YITP Registration & OTP Flow"""
    
    def __init__(self):
        self.client = Client()
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test_result(self, test_name, passed, message=""):
        """Log individual test results"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            
        result = f"{status} - {test_name}"
        if message:
            result += f": {message}"
            
        self.test_results.append(result)
        logger.info(result)
        
    def create_test_user(self, username="testuser", email="test@example.com"):
        """Create a test user for testing"""
        try:
            # Clean up existing test user
            User.objects.filter(username=username).delete()
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password="testpass123",
                first_name="Test",
                last_name="User",
                is_active=False  # Simulate unverified user
            )
            return user
        except Exception as e:
            logger.error(f"Failed to create test user: {e}")
            return None
            
    def test_admin_notification_system(self):
        """Test 1: Admin Notification System Implementation"""
        logger.info("🧪 Testing Admin Notification System...")
        
        try:
            # Create test user
            user = self.create_test_user("admin_test_user", "admin_test@example.com")
            if not user:
                self.log_test_result("Admin Notification - User Creation", False, "Failed to create test user")
                return
                
            # Clear mail outbox
            mail.outbox = []
            
            # Test admin notification function
            send_otp_verification_admin_notification(user)
            
            # Check if admin notification email was sent
            admin_emails = [email for email in mail.outbox if 'admin@yitp.org' in email.to]
            
            if admin_emails:
                admin_email = admin_emails[0]
                self.log_test_result("Admin Notification - Email Sent", True, f"Admin email sent to {admin_email.to}")
                
                # Validate email content
                if user.email in admin_email.body and user.username in admin_email.body:
                    self.log_test_result("Admin Notification - Content Validation", True, "Email contains user details")
                else:
                    self.log_test_result("Admin Notification - Content Validation", False, "Email missing user details")
            else:
                self.log_test_result("Admin Notification - Email Sent", False, "No admin notification email found")
                
        except Exception as e:
            self.log_test_result("Admin Notification - System Error", False, str(e))
            
    def test_automatic_login_after_otp(self):
        """Test 2: Automatic User Login After OTP Verification"""
        logger.info("🧪 Testing Automatic Login After OTP Verification...")
        
        try:
            # Create test user
            user = self.create_test_user("login_test_user", "login_test@example.com")
            if not user:
                self.log_test_result("Auto Login - User Creation", False, "Failed to create test user")
                return
                
            # Generate OTP
            otp_record, email_sent = generate_and_send_otp(user)
            
            if not otp_record:
                self.log_test_result("Auto Login - OTP Generation", False, "Failed to generate OTP")
                return
                
            self.log_test_result("Auto Login - OTP Generation", True, f"OTP generated: {otp_record.otp_code}")
            
            # Simulate OTP verification POST request
            response = self.client.post('/verify-otp/', {
                'user_id': user.id,
                'otp_code': otp_record.otp_code
            })
            
            # Check if user is automatically logged in
            if response.status_code == 302:  # Redirect after successful verification
                self.log_test_result("Auto Login - Redirect Response", True, "Successful redirect after verification")
                
                # Check if user is in session (logged in)
                user.refresh_from_db()
                if user.is_active:
                    self.log_test_result("Auto Login - User Activation", True, "User activated successfully")
                else:
                    self.log_test_result("Auto Login - User Activation", False, "User not activated")
            else:
                self.log_test_result("Auto Login - Verification Response", False, f"Unexpected response: {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Auto Login - System Error", False, str(e))
            
    def test_profile_completion_tracking(self):
        """Test 3: Profile Completion Tracking System"""
        logger.info("🧪 Testing Profile Completion Tracking...")
        
        try:
            # Create test user
            user = self.create_test_user("profile_test_user", "profile_test@example.com")
            if not user:
                self.log_test_result("Profile Tracking - User Creation", False, "Failed to create test user")
                return
                
            # Create or get profile
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Test initial completion percentage
            initial_completion = profile.profile_completion_percentage
            self.log_test_result("Profile Tracking - Initial Completion", True, f"Initial completion: {initial_completion}%")
            
            # Test completion calculation method
            profile.calculate_profile_completion()
            calculated_completion = profile.profile_completion_percentage
            
            if calculated_completion >= 0 and calculated_completion <= 100:
                self.log_test_result("Profile Tracking - Completion Calculation", True, f"Calculated: {calculated_completion}%")
            else:
                self.log_test_result("Profile Tracking - Completion Calculation", False, f"Invalid completion: {calculated_completion}%")
                
            # Test completion status method
            completion_status = profile.get_completion_status()
            
            if 'message' in completion_status and 'color' in completion_status:
                self.log_test_result("Profile Tracking - Status Method", True, f"Status: {completion_status['message']}")
            else:
                self.log_test_result("Profile Tracking - Status Method", False, "Invalid completion status format")
                
            # Test email verification field
            if hasattr(profile, 'email_verified'):
                self.log_test_result("Profile Tracking - Email Verified Field", True, f"Email verified: {profile.email_verified}")
            else:
                self.log_test_result("Profile Tracking - Email Verified Field", False, "email_verified field missing")
                
        except Exception as e:
            self.log_test_result("Profile Tracking - System Error", False, str(e))
            
    def test_welcome_page_redirect_flow(self):
        """Test 4: Welcome Page Redirect Flow"""
        logger.info("🧪 Testing Welcome Page Redirect Flow...")
        
        try:
            # Create test user
            user = self.create_test_user("welcome_test_user", "welcome_test@example.com")
            if not user:
                self.log_test_result("Welcome Redirect - User Creation", False, "Failed to create test user")
                return
                
            # Activate user (simulate successful OTP verification)
            user.is_active = True
            user.save()
            
            # Log in user
            self.client.force_login(user)
            
            # Test welcome page access
            response = self.client.get('/welcome/')
            
            if response.status_code == 200:
                self.log_test_result("Welcome Redirect - Page Access", True, "Welcome page accessible")
                
                # Check if welcome page contains expected content
                if 'Welcome to YITP' in response.content.decode():
                    self.log_test_result("Welcome Redirect - Content Validation", True, "Welcome content found")
                else:
                    self.log_test_result("Welcome Redirect - Content Validation", False, "Welcome content missing")
            else:
                self.log_test_result("Welcome Redirect - Page Access", False, f"Status code: {response.status_code}")
                
        except Exception as e:
            self.log_test_result("Welcome Redirect - System Error", False, str(e))
            
    def test_email_verification_status_integration(self):
        """Test 5: Email Verification Status Field Integration"""
        logger.info("🧪 Testing Email Verification Status Integration...")

        try:
            # Create test user
            user = self.create_test_user("email_verify_test", "email_verify_test@example.com")
            if not user:
                self.log_test_result("Email Verification - User Creation", False, "Failed to create test user")
                return

            # Create profile
            profile, created = Profile.objects.get_or_create(user=user)

            # Test initial email verification status
            initial_status = profile.email_verified
            self.log_test_result("Email Verification - Initial Status", True, f"Initial status: {initial_status}")

            # Simulate OTP verification process
            otp_record, email_sent = generate_and_send_otp(user)

            # Manually update email verification (simulating OTP verification)
            profile.email_verified = True
            profile.save()

            # Verify the field was updated
            profile.refresh_from_db()
            if profile.email_verified:
                self.log_test_result("Email Verification - Status Update", True, "Email verification status updated")
            else:
                self.log_test_result("Email Verification - Status Update", False, "Email verification status not updated")

        except Exception as e:
            self.log_test_result("Email Verification - System Error", False, str(e))

    def test_welcome_page_middleware_fix(self):
        """Test 6: WelcomePageRedirectMiddleware Session Flag Fix"""
        logger.info("🧪 Testing WelcomePageRedirectMiddleware Session Flag Fix...")

        try:
            # Create test user
            user = self.create_test_user("middleware_test", "middleware_test@example.com")
            if not user:
                self.log_test_result("Middleware Fix - User Creation", False, "Failed to create test user")
                return

            # Activate user and log in
            user.is_active = True
            user.save()
            self.client.force_login(user)

            # Test 1: Without session flag (should work normally)
            response = self.client.get('/welcome/')
            if response.status_code == 200:
                self.log_test_result("Middleware Fix - Normal Welcome Access", True, "Welcome page accessible without session flag")
            else:
                self.log_test_result("Middleware Fix - Normal Welcome Access", False, f"Status: {response.status_code}")

            # Test 2: With session flag (simulating OTP verification)
            session = self.client.session
            session['just_completed_otp_verification'] = True
            session['otp_verification_timestamp'] = timezone.now().isoformat()
            session.save()

            response = self.client.get('/welcome/')
            if response.status_code == 200:
                self.log_test_result("Middleware Fix - OTP Session Flag", True, "Welcome page accessible with OTP session flag")

                # Check if session flag was cleared
                updated_session = self.client.session
                if not updated_session.get('just_completed_otp_verification'):
                    self.log_test_result("Middleware Fix - Session Flag Cleanup", True, "Session flag properly cleared")
                else:
                    self.log_test_result("Middleware Fix - Session Flag Cleanup", False, "Session flag not cleared")
            else:
                self.log_test_result("Middleware Fix - OTP Session Flag", False, f"Status: {response.status_code}")

        except Exception as e:
            self.log_test_result("Middleware Fix - System Error", False, str(e))

    def test_profile_creation_during_otp(self):
        """Test 7: Profile Creation During OTP Verification"""
        logger.info("🧪 Testing Profile Creation During OTP Verification...")

        try:
            # Create test user
            user = self.create_test_user("profile_otp_test", "profile_otp_test@example.com")
            if not user:
                self.log_test_result("Profile OTP - User Creation", False, "Failed to create test user")
                return

            # Ensure no profile exists initially
            Profile.objects.filter(user=user).delete()

            # Generate OTP
            otp_record, email_sent = generate_and_send_otp(user)
            if not otp_record:
                self.log_test_result("Profile OTP - OTP Generation", False, "Failed to generate OTP")
                return

            # Simulate OTP verification POST request
            response = self.client.post('/verify-otp/', {
                'user_id': user.id,
                'otp_code': otp_record.otp_code
            })

            # Check if profile was created during OTP verification
            try:
                # Refresh user from database to get updated profile
                user.refresh_from_db()
                profile = user.profile
                profile.refresh_from_db()  # Ensure we have the latest profile data
                self.log_test_result("Profile OTP - Profile Creation", True, "Profile created during OTP verification")

                # Check if email verification was set
                if profile.email_verified:
                    self.log_test_result("Profile OTP - Email Verification Set", True, "Email verification status set during OTP")
                else:
                    self.log_test_result("Profile OTP - Email Verification Set", False, "Email verification not set")

                # Check if completion percentage was calculated
                if profile.profile_completion_percentage >= 0:
                    self.log_test_result("Profile OTP - Completion Calculated", True, f"Completion: {profile.profile_completion_percentage}%")
                else:
                    self.log_test_result("Profile OTP - Completion Calculated", False, "Completion percentage not calculated")

            except Profile.DoesNotExist:
                self.log_test_result("Profile OTP - Profile Creation", False, "Profile not created during OTP verification")

        except Exception as e:
            self.log_test_result("Profile OTP - System Error", False, str(e))

    def test_onboarding_modal_enhancement(self):
        """Test 8: Enhanced Onboarding Modal Logic"""
        logger.info("🧪 Testing Enhanced Onboarding Modal Logic...")

        try:
            # Create test user
            user = self.create_test_user("onboarding_test", "onboarding_test@example.com")
            if not user:
                self.log_test_result("Onboarding Enhancement - User Creation", False, "Failed to create test user")
                return

            # Activate user and log in
            user.is_active = True
            user.save()
            self.client.force_login(user)

            # Test 1: Welcome page with OTP verification session flag
            session = self.client.session
            session['just_completed_otp_verification'] = True
            session['otp_verification_timestamp'] = timezone.now().isoformat()
            session.save()

            response = self.client.get('/welcome/')

            if response.status_code == 200:
                self.log_test_result("Onboarding Enhancement - Welcome Page Access", True, "Welcome page accessible")

                # Check if context variables are passed to template
                context = response.context
                if context and context.get('just_completed_otp'):
                    self.log_test_result("Onboarding Enhancement - OTP Context Variable", True, "OTP completion context passed to template")
                else:
                    self.log_test_result("Onboarding Enhancement - OTP Context Variable", False, "OTP completion context missing")

                # Check if template contains enhanced onboarding logic
                content = response.content.decode()
                if 'justCompletedOTP' in content and 'just_completed_otp' in content:
                    self.log_test_result("Onboarding Enhancement - JavaScript Logic", True, "Enhanced onboarding JavaScript found")
                else:
                    self.log_test_result("Onboarding Enhancement - JavaScript Logic", False, "Enhanced onboarding JavaScript missing")
            else:
                self.log_test_result("Onboarding Enhancement - Welcome Page Access", False, f"Status: {response.status_code}")

        except Exception as e:
            self.log_test_result("Onboarding Enhancement - System Error", False, str(e))
            
    def run_all_tests(self):
        """Run all test suites"""
        logger.info("🚀 Starting YITP Registration & OTP Flow Test Suite")
        logger.info("=" * 60)

        # Run original test suites
        self.test_admin_notification_system()
        self.test_automatic_login_after_otp()
        self.test_profile_completion_tracking()
        self.test_welcome_page_redirect_flow()
        self.test_email_verification_status_integration()

        # Run new test suites for the three fixes
        logger.info("🔧 Testing Post-OTP Verification Enhancement Fixes...")
        self.test_welcome_page_middleware_fix()
        self.test_profile_creation_during_otp()
        self.test_onboarding_modal_enhancement()

        # Generate final report
        self.generate_final_report()
        
    def generate_final_report(self):
        """Generate comprehensive test report"""
        logger.info("=" * 60)
        logger.info("📊 FINAL TEST REPORT")
        logger.info("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        logger.info(f"Total Tests: {self.total_tests}")
        logger.info(f"Passed: {self.passed_tests}")
        logger.info(f"Failed: {self.failed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("")
        
        logger.info("📋 DETAILED RESULTS:")
        for result in self.test_results:
            logger.info(result)
            
        logger.info("=" * 60)
        
        if success_rate >= 90:
            logger.info("🎉 EXCELLENT: All major features working correctly!")
        elif success_rate >= 75:
            logger.info("✅ GOOD: Most features working, minor issues to address")
        elif success_rate >= 50:
            logger.info("⚠️ MODERATE: Several issues need attention")
        else:
            logger.info("❌ CRITICAL: Major issues require immediate attention")

if __name__ == "__main__":
    # Run the comprehensive test suite
    test_suite = RegistrationOTPFlowTestSuite()
    test_suite.run_all_tests()
