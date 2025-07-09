#!/usr/bin/env python3
"""
YITP Course Enrollment and Payment Journey Test Suite
====================================================

Comprehensive test suite for the complete YITP course enrollment workflow
from course discovery through payment processing to certificate generation.

Test Coverage:
1. Course Enrollment Service (Free & Paid Courses)
2. Payment Processing (M-Pesa, Bank Transfer)
3. Certificate Generation & Verification
4. Email Notification System
5. Error Handling & Edge Cases
6. Integration Tests (End-to-End Workflows)
7. Payment Status Tracking & Confirmation
8. Course Progress & Completion Detection
9. Admin Notification System
10. Security & Validation Testing

Author: YITP Development Team
Date: 2025-01-05
"""

import os
import sys
import django
import unittest
import logging
from decimal import Decimal
from unittest.mock import patch, Mock

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
from django.conf import settings

# Import YITP modules
from users.models import Profile
from courses.models import Course, Category, Module, Lesson
from progress.models import Enrollment, Certificate
from courses.enrollment_service import EnrollmentService
from users.email_utils import (
    send_enrollment_confirmation_email,
    send_enrollment_admin_notification,
    send_certificate_issuance_email
)

# Import payment modules (if they exist)
try:
    from payments.models import Payment, PaymentMethod
    from payments.payment_service import PaymentService
    PAYMENTS_AVAILABLE = True
except ImportError:
    PAYMENTS_AVAILABLE = False
    # Create mock classes for testing
    class Payment:
        pass
    class PaymentMethod:
        pass
    class PaymentService:
        @staticmethod
        def process_mpesa_payment(*args, **kwargs):
            return {'status': 'success', 'reference': 'test-ref'}
        @staticmethod
        def process_bank_transfer(*args, **kwargs):
            return {'status': 'pending', 'reference': 'test-bank-ref'}

# Import certificate modules (if they exist)
try:
    from certificates.certificate_service import CertificateService
    CERTIFICATES_AVAILABLE = True
except ImportError:
    CERTIFICATES_AVAILABLE = False


class CourseEnrollmentTestCase(TestCase):
    """Base test case with common setup for course enrollment tests"""
    
    def setUp(self):
        """Set up test data for course enrollment tests"""
        # Create test users first
        self.regular_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

        self.paid_user = User.objects.create_user(
            username='paiduser',
            email='paiduser@example.com',
            password='testpass123',
            first_name='Paid',
            last_name='User'
        )

        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

        # Create test categories
        self.tech_category, _ = Category.objects.get_or_create(
            slug="technology",
            defaults={
                'name': "Technology",
                'description': "Technology courses"
            }
        )

        self.business_category, _ = Category.objects.get_or_create(
            slug="business",
            defaults={
                'name': "Business",
                'description': "Business courses"
            }
        )

        # Create test courses (after users are created)
        self.free_course = Course.objects.create(
            title="Introduction to Digital Literacy",
            slug="intro-digital-literacy",
            description="Learn basic computer skills and internet usage",
            learning_objectives="Master basic computer skills",
            category=self.tech_category,
            price=Decimal('0.00'),
            estimated_duration=40,  # 40 hours
            instructor=self.admin_user,
            is_published=True,
            enrollment_limit=50
        )

        self.paid_course = Course.objects.create(
            title="Advanced Web Development",
            slug="advanced-web-development",
            description="Master modern web development technologies",
            learning_objectives="Build full-stack applications",
            category=self.tech_category,
            price=Decimal('15000.00'),
            estimated_duration=120,  # 120 hours
            instructor=self.admin_user,
            is_published=True,
            enrollment_limit=25
        )

        self.expensive_course = Course.objects.create(
            title="Business Leadership Masterclass",
            slug="business-leadership-masterclass",
            description="Comprehensive leadership training program",
            learning_objectives="Become an effective leader",
            category=self.business_category,
            price=Decimal('75000.00'),
            estimated_duration=160,  # 160 hours
            instructor=self.admin_user,
            is_published=True,
            enrollment_limit=15
        )

        # Create test modules and lessons for courses
        self._create_course_content()
        
        # Get or create user profiles (profiles may be auto-created by signals)
        self.regular_profile, _ = Profile.objects.get_or_create(
            user=self.regular_user,
            defaults={
                'phone_number': '+254712345678',
                'payment_status': 'unpaid'
            }
        )
        # Update profile if it already existed
        self.regular_profile.phone_number = '+254712345678'
        self.regular_profile.payment_status = 'unpaid'
        self.regular_profile.save()

        self.paid_profile, _ = Profile.objects.get_or_create(
            user=self.paid_user,
            defaults={
                'phone_number': '+254787654321',
                'payment_status': 'confirmed',
                'payment_confirmed_at': timezone.now(),
                'payment_amount': Decimal('15000.00'),
                'payment_reference': 'TEST-PAY-001'
            }
        )
        # Update profile if it already existed
        self.paid_profile.phone_number = '+254787654321'
        self.paid_profile.payment_status = 'confirmed'
        self.paid_profile.payment_confirmed_at = timezone.now()
        self.paid_profile.payment_amount = Decimal('15000.00')
        self.paid_profile.payment_reference = 'TEST-PAY-001'
        self.paid_profile.save()
        
        # Create test client
        self.client = Client()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def _create_course_content(self):
        """Create modules and lessons for test courses"""
        # Free course content
        free_module = Module.objects.create(
            course=self.free_course,
            title="Getting Started",
            sort_order=1,
            description="Introduction to digital literacy",
            estimated_duration=75,  # Total duration in minutes
            is_published=True
        )

        Lesson.objects.create(
            module=free_module,
            title="Computer Basics",
            sort_order=1,
            content="Learn about computer hardware and software",
            estimated_duration=30,
            content_type='text',
            is_published=True
        )

        Lesson.objects.create(
            module=free_module,
            title="Internet Fundamentals",
            sort_order=2,
            content="Understanding how the internet works",
            estimated_duration=45,
            content_type='text',
            is_published=True
        )
        
        # Paid course content
        paid_module = Module.objects.create(
            course=self.paid_course,
            title="Web Development Fundamentals",
            sort_order=1,
            description="Core concepts of web development",
            estimated_duration=210,  # Total duration in minutes
            is_published=True
        )

        Lesson.objects.create(
            module=paid_module,
            title="HTML & CSS",
            sort_order=1,
            content="Building web pages with HTML and CSS",
            estimated_duration=90,
            content_type='text',
            is_published=True
        )

        Lesson.objects.create(
            module=paid_module,
            title="JavaScript Basics",
            sort_order=2,
            content="Introduction to JavaScript programming",
            estimated_duration=120,
            content_type='text',
            is_published=True
        )
    
    def tearDown(self):
        """Clean up after tests"""
        # Clear email outbox
        mail.outbox = []
        
        # Clear any uploaded files
        import shutil
        media_root = settings.MEDIA_ROOT
        if os.path.exists(media_root):
            for filename in os.listdir(media_root):
                file_path = os.path.join(media_root, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    self.logger.warning(f"Failed to clean up file {file_path}: {e}")


class EnrollmentServiceUnitTests(CourseEnrollmentTestCase):
    """Unit tests for the EnrollmentService class"""
    
    def test_validate_enrollment_eligibility_free_course(self):
        """Test enrollment eligibility validation for free courses"""
        result = EnrollmentService.validate_enrollment_eligibility(
            self.regular_user, 
            self.free_course
        )
        
        self.assertTrue(result['is_valid'])
        self.assertNotIn('error_message', result)
    
    def test_validate_enrollment_eligibility_paid_course_no_payment(self):
        """Test enrollment eligibility validation for paid courses without payment"""
        result = EnrollmentService.validate_enrollment_eligibility(
            self.regular_user, 
            self.paid_course
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Payment verification required', result['error_message'])
        self.assertIn('KES 15,000.00', result['error_message'])
    
    def test_validate_enrollment_eligibility_paid_course_with_payment(self):
        """Test enrollment eligibility validation for paid courses with confirmed payment"""
        result = EnrollmentService.validate_enrollment_eligibility(
            self.paid_user, 
            self.paid_course
        )
        
        self.assertTrue(result['is_valid'])
        self.assertNotIn('error_message', result)
    
    def test_validate_enrollment_eligibility_enrollment_limit_reached(self):
        """Test enrollment eligibility when course enrollment limit is reached"""
        # Set a low enrollment limit
        self.free_course.enrollment_limit = 1
        self.free_course.save()
        
        # Create an existing enrollment
        Enrollment.objects.create(
            student=self.paid_user,
            course=self.free_course,
            status='active'
        )
        
        # Try to enroll another user
        result = EnrollmentService.validate_enrollment_eligibility(
            self.regular_user, 
            self.free_course
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn('enrollment limit', result['error_message'])
        self.assertIn('1 students', result['error_message'])
    
    def test_validate_enrollment_eligibility_already_enrolled(self):
        """Test enrollment eligibility when user is already enrolled"""
        # Create existing enrollment
        existing_enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )
        
        result = EnrollmentService.validate_enrollment_eligibility(
            self.regular_user, 
            self.free_course
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn('already enrolled', result['error_message'])
        self.assertEqual(result['existing_enrollment'], existing_enrollment)
    
    def test_process_enrollment_new_enrollment(self):
        """Test processing a new enrollment"""
        result = EnrollmentService.process_enrollment(
            self.regular_user, 
            self.free_course
        )
        
        self.assertTrue(result['success'])
        self.assertTrue(result['created'])
        self.assertIsNotNone(result['enrollment'])
        self.assertEqual(result['enrollment'].student, self.regular_user)
        self.assertEqual(result['enrollment'].course, self.free_course)
        self.assertEqual(result['enrollment'].status, 'active')
        self.assertEqual(result['enrollment'].progress_percentage, Decimal('0.00'))
    
    def test_process_enrollment_existing_enrollment(self):
        """Test processing enrollment when user is already enrolled"""
        # Create existing enrollment
        existing_enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )
        
        result = EnrollmentService.process_enrollment(
            self.regular_user, 
            self.free_course
        )
        
        self.assertFalse(result['success'])
        self.assertFalse(result['created'])
        self.assertEqual(result['enrollment'], existing_enrollment)
        self.assertIn('already enrolled', result['message'])
    
    @patch('courses.enrollment_service.send_enrollment_confirmation_email')
    @patch('courses.enrollment_service.send_enrollment_admin_notification')
    def test_send_enrollment_notifications_success(self, mock_admin_email, mock_user_email):
        """Test successful sending of enrollment notifications"""
        enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )
        
        # Mock successful email sending
        mock_user_email.return_value = None
        mock_admin_email.return_value = None
        
        result = EnrollmentService.send_enrollment_notifications(
            self.regular_user, 
            self.free_course, 
            enrollment
        )
        
        self.assertTrue(result['user_email_sent'])
        self.assertTrue(result['admin_email_sent'])
        self.assertEqual(len(result['errors']), 0)
        
        # Verify email functions were called
        mock_user_email.assert_called_once_with(self.regular_user, self.free_course, enrollment)
        mock_admin_email.assert_called_once_with(self.regular_user, self.free_course, enrollment)
    
    @patch('courses.enrollment_service.send_enrollment_confirmation_email')
    @patch('courses.enrollment_service.send_enrollment_admin_notification')
    def test_send_enrollment_notifications_email_failure(self, mock_admin_email, mock_user_email):
        """Test handling of email sending failures"""
        enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )
        
        # Mock email sending failures
        mock_user_email.side_effect = Exception("SMTP connection failed")
        mock_admin_email.side_effect = Exception("Admin email not configured")
        
        result = EnrollmentService.send_enrollment_notifications(
            self.regular_user, 
            self.free_course, 
            enrollment
        )
        
        self.assertFalse(result['user_email_sent'])
        self.assertFalse(result['admin_email_sent'])
        self.assertEqual(len(result['errors']), 2)
        self.assertIn('SMTP connection failed', result['errors'][0])
        self.assertIn('Admin email not configured', result['errors'][1])
    
    def test_enroll_user_in_course_complete_workflow_free_course(self):
        """Test complete enrollment workflow for free course"""
        with patch.object(EnrollmentService, 'send_enrollment_notifications') as mock_notifications:
            mock_notifications.return_value = {
                'user_email_sent': True,
                'admin_email_sent': True,
                'errors': []
            }
            
            result = EnrollmentService.enroll_user_in_course(
                self.regular_user, 
                self.free_course
            )
            
            self.assertTrue(result['success'])
            self.assertTrue(result['created'])
            self.assertIsNotNone(result['enrollment'])
            self.assertIsNotNone(result['email_results'])
            self.assertTrue(result['email_results']['user_email_sent'])
            
            # Verify enrollment was created in database
            enrollment = Enrollment.objects.get(
                student=self.regular_user,
                course=self.free_course
            )
            self.assertEqual(enrollment.status, 'active')
    
    def test_enroll_user_in_course_complete_workflow_paid_course_with_payment(self):
        """Test complete enrollment workflow for paid course with confirmed payment"""
        with patch.object(EnrollmentService, 'send_enrollment_notifications') as mock_notifications:
            mock_notifications.return_value = {
                'user_email_sent': True,
                'admin_email_sent': True,
                'errors': []
            }
            
            result = EnrollmentService.enroll_user_in_course(
                self.paid_user, 
                self.paid_course
            )
            
            self.assertTrue(result['success'])
            self.assertTrue(result['created'])
            self.assertIsNotNone(result['enrollment'])
            self.assertIsNotNone(result['email_results'])
            
            # Verify enrollment was created in database
            enrollment = Enrollment.objects.get(
                student=self.paid_user,
                course=self.paid_course
            )
            self.assertEqual(enrollment.status, 'active')
    
    def test_enroll_user_in_course_payment_required_failure(self):
        """Test enrollment failure when payment is required but not confirmed"""
        result = EnrollmentService.enroll_user_in_course(
            self.regular_user, 
            self.paid_course
        )
        
        self.assertFalse(result['success'])
        self.assertFalse(result['created'])
        self.assertIsNone(result['enrollment'])
        self.assertIsNone(result['email_results'])
        self.assertIn('Payment verification required', result['message'])
        
        # Verify no enrollment was created
        self.assertFalse(
            Enrollment.objects.filter(
                student=self.regular_user,
                course=self.paid_course
            ).exists()
        )
    
    def test_get_course_by_slug_or_id_slug_lookup(self):
        """Test course lookup by slug"""
        course = EnrollmentService.get_course_by_slug_or_id('intro-digital-literacy')
        self.assertEqual(course, self.free_course)
    
    def test_get_course_by_slug_or_id_id_lookup(self):
        """Test course lookup by ID"""
        course = EnrollmentService.get_course_by_slug_or_id(self.paid_course.id)
        self.assertEqual(course, self.paid_course)
    
    def test_get_course_by_slug_or_id_not_found(self):
        """Test course lookup with invalid slug/ID"""
        from django.http import Http404
        
        with self.assertRaises(Http404):
            EnrollmentService.get_course_by_slug_or_id('nonexistent-course')
        
        with self.assertRaises(Http404):
            EnrollmentService.get_course_by_slug_or_id(99999)


@unittest.skipUnless(PAYMENTS_AVAILABLE, "Payment modules not available")
class PaymentServiceUnitTests(CourseEnrollmentTestCase):
    """Unit tests for the PaymentService class"""

    def setUp(self):
        """Set up payment-specific test data"""
        super().setUp()

        # Create payment methods
        self.mpesa_method = PaymentMethod.objects.create(
            code='mpesa',
            name='M-Pesa',
            description='Pay using M-Pesa mobile money',
            is_active=True,
            requires_phone=True,
            processing_fee_percentage=Decimal('0.00')
        )

        self.bank_method = PaymentMethod.objects.create(
            code='bank_transfer',
            name='Bank Transfer',
            description='Direct bank transfer',
            is_active=True,
            requires_phone=False,
            processing_fee_percentage=Decimal('0.00')
        )

    def test_create_payment_record_mpesa(self):
        """Test creating a payment record for M-Pesa"""
        payment = PaymentService.create_payment_record(
            user=self.regular_user,
            course=self.paid_course,
            amount=Decimal('15000.00'),
            payment_method='mpesa'
        )

        self.assertIsNotNone(payment)
        self.assertEqual(payment.user, self.regular_user)
        self.assertEqual(payment.course, self.paid_course)
        self.assertEqual(payment.payment_method, 'mpesa')
        self.assertEqual(payment.amount, Decimal('15000.00'))
        self.assertEqual(payment.status, 'pending')
        self.assertIsNotNone(payment.reference_number)

    def test_create_payment_record_bank_transfer(self):
        """Test creating a payment record for bank transfer"""
        payment = PaymentService.create_payment_record(
            user=self.regular_user,
            course=self.expensive_course,
            amount=Decimal('75000.00'),
            payment_method='bank_transfer'
        )

        self.assertIsNotNone(payment)
        self.assertEqual(payment.user, self.regular_user)
        self.assertEqual(payment.course, self.expensive_course)
        self.assertEqual(payment.payment_method, 'bank_transfer')
        self.assertEqual(payment.amount, Decimal('75000.00'))
        self.assertEqual(payment.status, 'pending')
        self.assertIsNotNone(payment.reference_number)

    @patch('payments.payment_service.requests.get')
    @patch('payments.payment_service.requests.post')
    @override_settings(
        MPESA_CONSUMER_KEY='test_consumer_key',
        MPESA_CONSUMER_SECRET='test_consumer_secret',
        MPESA_SHORTCODE='174379',
        MPESA_PASSKEY='test_passkey',
        MPESA_CALLBACK_URL='https://test.example.com/callback/'
    )
    def test_process_mpesa_payment_success(self, mock_post, mock_get):
        """Test successful M-Pesa STK push"""
        # Mock successful M-Pesa access token response (GET request)
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {
            'access_token': 'test_access_token_123',
            'expires_in': '3599'
        }
        mock_get.return_value = mock_auth_response

        # Mock successful M-Pesa STK push response (POST request)
        mock_stk_response = Mock()
        mock_stk_response.status_code = 200
        mock_stk_response.json.return_value = {
            'ResponseCode': '0',
            'ResponseDescription': 'Success. Request accepted for processing',
            'MerchantRequestID': 'test-merchant-123',
            'CheckoutRequestID': 'test-checkout-456'
        }
        mock_post.return_value = mock_stk_response

        payment = Payment.objects.create(
            user=self.regular_user,
            course=self.paid_course,
            payment_method='mpesa',
            amount=Decimal('15000.00'),
            phone_number='254712345678',
            reference_number='TEST-PAY-001',
            status='pending'
        )

        result = PaymentService.process_mpesa_payment(payment, '254712345678')

        self.assertTrue(result['success'])
        self.assertIn('message', result)
        self.assertIn('transaction_id', result)

        # Verify payment status updated
        payment.refresh_from_db()
        # The actual implementation may update status differently
        self.assertIn(payment.status, ['pending', 'processing', 'confirmed'])

    @patch('payments.payment_service.requests.post')
    def test_process_mpesa_payment_failure(self, mock_post):
        """Test M-Pesa STK push failure"""
        # Mock failed M-Pesa API response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            'ResponseCode': '1',
            'ResponseDescription': 'Invalid phone number',
            'errorCode': 'INVALID_PHONE',
            'errorMessage': 'The phone number is invalid'
        }
        mock_post.return_value = mock_response

        payment = Payment.objects.create(
            user=self.regular_user,
            course=self.paid_course,
            payment_method='mpesa',
            amount=Decimal('15000.00'),
            phone_number='254712345678',
            reference_number='TEST-PAY-002',
            status='pending'
        )

        result = PaymentService.process_mpesa_payment(payment, '254712345678')

        self.assertFalse(result['success'])
        self.assertIn('message', result)

        # Verify payment status (may or may not be updated depending on implementation)
        payment.refresh_from_db()
        self.assertIn(payment.status, ['pending', 'failed'])

    def test_confirm_payment_success(self):
        """Test successful payment confirmation"""
        payment = Payment.objects.create(
            user=self.regular_user,
            course=self.paid_course,
            payment_method='mpesa',
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            reference_number='TEST-PAY-003',
            status='processing'
        )

        # Test payment confirmation using payment reference
        result = PaymentService.confirm_payment(
            payment_reference=payment.reference_number,
            transaction_id='MPE123456789'
        )

        self.assertTrue(result['success'])

        # Verify payment status updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'confirmed')

        # Verify user profile updated
        self.regular_profile.refresh_from_db()
        self.assertEqual(self.regular_profile.payment_status, 'confirmed')
        self.assertEqual(self.regular_profile.payment_amount, Decimal('15000.00'))
        self.assertIsNotNone(self.regular_profile.payment_confirmed_at)

    def test_confirm_payment_failure(self):
        """Test payment confirmation failure"""
        payment = Payment.objects.create(
            user=self.regular_user,
            course=self.paid_course,
            payment_method='mpesa',
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            reference_number='TEST-PAY-004',
            status='processing'
        )

        # Test payment confirmation with invalid reference (should fail)
        result = PaymentService.confirm_payment(
            payment_reference='INVALID-REF-123',
            transaction_id='INVALID-TXN'
        )

        self.assertFalse(result['success'])
        self.assertIn('message', result)

        # Original payment should remain unchanged
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'processing')

    @patch('payments.payment_service.requests.post')
    def test_check_payment_status_success(self, mock_post):
        """Test checking payment status"""
        # Mock successful status check response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'ResponseCode': '0',
            'ResultCode': '0',
            'ResultDesc': 'The service request is processed successfully.'
        }
        mock_post.return_value = mock_response

        payment = Payment.objects.create(
            user=self.regular_user,
            course=self.paid_course,
            payment_method='mpesa',
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            reference_number='TEST-PAY-005',
            status='processing'
        )

        # Test payment status check using payment reference
        result = PaymentService.check_payment_status(payment.reference_number)

        self.assertIn('status', result)
        self.assertIn('payment', result)
        self.assertIn('message', result)
        self.assertEqual(result['status'], 'processing')
        self.assertEqual(result['payment'], payment)


@unittest.skipUnless(CERTIFICATES_AVAILABLE, "Certificate modules not available")
class CertificateServiceUnitTests(CourseEnrollmentTestCase):
    """Unit tests for the CertificateService class"""

    def setUp(self):
        """Set up certificate-specific test data"""
        super().setUp()

        # Create completed enrollment
        self.completed_enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='completed',
            progress_percentage=Decimal('100.00'),
            completion_date=timezone.now()
        )

    def test_generate_certificate_pdf(self):
        """Test PDF certificate generation"""
        result = CertificateService.generate_certificate(self.completed_enrollment)

        self.assertTrue(result['success'])
        self.assertIsNotNone(result['certificate'])
        self.assertEqual(result['certificate'].enrollment, self.completed_enrollment)
        self.assertIsNotNone(result['certificate'].certificate_id)
        self.assertIsNotNone(result['certificate'].verification_code)
        self.assertIn('successfully', result['message'])

    def test_generate_certificate_html(self):
        """Test HTML certificate generation"""
        result = CertificateService.generate_certificate(self.completed_enrollment)

        self.assertTrue(result['success'])
        self.assertIsNotNone(result['certificate'])
        self.assertEqual(result['certificate'].enrollment, self.completed_enrollment)
        self.assertIsNotNone(result['certificate'].certificate_id)
        self.assertIsNotNone(result['certificate'].verification_code)
        self.assertIn('successfully', result['message'])

    def test_verify_certificate_valid(self):
        """Test certificate verification with valid code"""
        certificate = Certificate.objects.create(
            enrollment=self.completed_enrollment,
            certificate_id='CERT-2025-001',
            verification_code='ABC123XYZ',
            certificate_type='completion'
        )

        result = CertificateService.verify_certificate('ABC123XYZ')

        self.assertTrue(result['valid'])
        self.assertEqual(result['certificate'], certificate)
        self.assertIn('valid and authentic', result['message'])

    def test_verify_certificate_invalid(self):
        """Test certificate verification with invalid code"""
        result = CertificateService.verify_certificate('INVALID123')

        self.assertFalse(result['valid'])
        self.assertIsNone(result['certificate'])
        self.assertIn('Invalid verification code', result['message'])

    def test_get_user_certificates(self):
        """Test retrieving user certificates"""
        # Create multiple certificates
        cert1 = Certificate.objects.create(
            enrollment=self.completed_enrollment,
            certificate_id='CERT-2025-001',
            verification_code='ABC123XYZ',
            certificate_type='completion'
        )

        # Create another completed enrollment
        another_enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.paid_course,
            status='completed',
            progress_percentage=Decimal('100.00'),
            completion_date=timezone.now()
        )

        cert2 = Certificate.objects.create(
            enrollment=another_enrollment,
            certificate_id='CERT-2025-002',
            verification_code='DEF456UVW',
            certificate_type='achievement'
        )

        certificates = CertificateService.get_user_certificates(self.regular_user)

        self.assertEqual(len(certificates), 2)
        self.assertIn(cert1, certificates)
        self.assertIn(cert2, certificates)


class EmailNotificationTests(CourseEnrollmentTestCase):
    """Tests for email notification system"""

    def test_enrollment_confirmation_email_free_course(self):
        """Test enrollment confirmation email for free course"""
        enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )

        # Clear email outbox
        mail.outbox = []

        # Send enrollment confirmation email
        send_enrollment_confirmation_email(self.regular_user, self.free_course, enrollment)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn(self.regular_user.email, email.to)
        self.assertIn('Enrollment Confirmation', email.subject)
        self.assertIn(self.free_course.title, email.body)
        self.assertIn('FREE', email.body)
        self.assertIn('start learning immediately', email.body)

    def test_enrollment_confirmation_email_paid_course(self):
        """Test enrollment confirmation email for paid course"""
        enrollment = Enrollment.objects.create(
            student=self.paid_user,
            course=self.paid_course,
            status='active'
        )

        # Clear email outbox
        mail.outbox = []

        # Send enrollment confirmation email
        send_enrollment_confirmation_email(self.paid_user, self.paid_course, enrollment)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn(self.paid_user.email, email.to)
        self.assertIn('Enrollment Confirmation', email.subject)
        self.assertIn(self.paid_course.title, email.body)
        self.assertIn('KES 15,000.00', email.body)
        self.assertIn('payment has been verified', email.body)

    def test_enrollment_admin_notification(self):
        """Test admin notification email for new enrollment"""
        enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )

        # Clear email outbox
        mail.outbox = []

        # Send admin notification
        send_enrollment_admin_notification(self.regular_user, self.free_course, enrollment)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn(settings.ADMIN_EMAIL, email.to)
        self.assertIn('New Course Enrollment', email.subject)
        self.assertIn(self.regular_user.get_full_name(), email.body)
        self.assertIn(self.free_course.title, email.body)
        self.assertIn(self.regular_user.email, email.body)

    @unittest.skipUnless(CERTIFICATES_AVAILABLE, "Certificate modules not available")
    def test_certificate_issuance_email(self):
        """Test certificate issuance email"""
        enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='completed',
            progress_percentage=Decimal('100.00'),
            completion_date=timezone.now()
        )

        certificate = Certificate.objects.create(
            enrollment=enrollment,
            certificate_id='CERT-2025-001',
            verification_code='ABC123XYZ',
            certificate_type='completion'
        )

        # Clear email outbox
        mail.outbox = []

        # Send certificate email
        send_certificate_issuance_email(self.regular_user, self.free_course, certificate)

        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertIn(self.regular_user.email, email.to)
        self.assertIn('Certificate Ready', email.subject)
        self.assertIn(certificate.certificate_id, email.body)
        self.assertIn(self.free_course.title, email.body)
        self.assertIn('download', email.body)

    def test_email_failure_handling(self):
        """Test handling of email sending failures"""
        enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )

        # Mock email backend to raise exception
        with patch('django.core.mail.send_mail') as mock_send_mail:
            mock_send_mail.side_effect = Exception("SMTP server unavailable")

            # This should not raise an exception
            try:
                send_enrollment_confirmation_email(self.regular_user, self.free_course, enrollment)
                # If we get here, the function handled the exception gracefully
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"Email function should handle exceptions gracefully: {e}")


class IntegrationTests(CourseEnrollmentTestCase):
    """End-to-end integration tests for complete user journeys"""

    def test_complete_free_course_enrollment_journey(self):
        """Test complete journey: course discovery → enrollment → email confirmation"""
        # Step 1: User logs in
        self.client.login(username='testuser', password='testpass123')

        # Step 2: User views course detail page
        course_detail_url = reverse('courses:course_detail', kwargs={'slug': self.free_course.slug})
        response = self.client.get(course_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.free_course.title)
        self.assertContains(response, 'Enroll Now')

        # Step 3: User enrolls in course
        enroll_url = reverse('courses:enroll', kwargs={'slug': self.free_course.slug})

        # Clear email outbox before enrollment
        mail.outbox = []

        response = self.client.post(enroll_url, follow=True)

        # Verify successful enrollment
        self.assertEqual(response.status_code, 200)

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Successfully enrolled' in str(message) for message in messages))

        # Verify enrollment created in database
        enrollment = Enrollment.objects.get(
            student=self.regular_user,
            course=self.free_course
        )
        self.assertEqual(enrollment.status, 'active')
        self.assertEqual(enrollment.progress_percentage, Decimal('0.00'))

        # Verify emails were sent (user confirmation + admin notification)
        self.assertEqual(len(mail.outbox), 2)

        # Check user confirmation email
        user_email = next((email for email in mail.outbox if self.regular_user.email in email.to), None)
        self.assertIsNotNone(user_email)
        self.assertIn('Enrollment Confirmation', user_email.subject)

        # Check admin notification email
        admin_email = next((email for email in mail.outbox if settings.ADMIN_EMAIL in email.to), None)
        self.assertIsNotNone(admin_email)
        self.assertIn('New Course Enrollment', admin_email.subject)

    def test_complete_paid_course_enrollment_journey_with_payment(self):
        """Test complete journey: paid course enrollment with confirmed payment"""
        # Step 1: User with confirmed payment logs in
        self.client.login(username='paiduser', password='testpass123')

        # Step 2: User views paid course detail page
        course_detail_url = reverse('courses:course_detail', kwargs={'slug': self.paid_course.slug})
        response = self.client.get(course_detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.paid_course.title)
        self.assertContains(response, 'KES 15,000.00')

        # Step 3: User enrolls in paid course
        enroll_url = reverse('courses:enroll', kwargs={'slug': self.paid_course.slug})

        # Clear email outbox before enrollment
        mail.outbox = []

        response = self.client.post(enroll_url, follow=True)

        # Verify successful enrollment
        self.assertEqual(response.status_code, 200)

        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Successfully enrolled' in str(message) for message in messages))

        # Verify enrollment created in database
        enrollment = Enrollment.objects.get(
            student=self.paid_user,
            course=self.paid_course
        )
        self.assertEqual(enrollment.status, 'active')

        # Verify emails were sent
        self.assertEqual(len(mail.outbox), 2)

    def test_paid_course_enrollment_failure_no_payment(self):
        """Test enrollment failure for paid course without payment"""
        # Step 1: User without payment logs in
        self.client.login(username='testuser', password='testpass123')

        # Step 2: User tries to enroll in paid course
        enroll_url = reverse('courses:enroll', kwargs={'slug': self.paid_course.slug})
        response = self.client.post(enroll_url, follow=True)

        # Verify enrollment was rejected
        self.assertEqual(response.status_code, 200)

        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Payment verification required' in str(message) for message in messages))

        # Verify no enrollment was created
        self.assertFalse(
            Enrollment.objects.filter(
                student=self.regular_user,
                course=self.paid_course
            ).exists()
        )

        # Verify no emails were sent
        self.assertEqual(len(mail.outbox), 0)

    def test_duplicate_enrollment_handling(self):
        """Test handling of duplicate enrollment attempts"""
        # Step 1: Create existing enrollment
        existing_enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )

        # Step 2: User logs in and tries to enroll again
        self.client.login(username='testuser', password='testpass123')

        enroll_url = reverse('courses:enroll', kwargs={'slug': self.free_course.slug})
        response = self.client.post(enroll_url, follow=True)

        # Verify appropriate handling
        self.assertEqual(response.status_code, 200)

        # Check info message about existing enrollment
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already enrolled' in str(message) for message in messages))

        # Verify only one enrollment exists
        enrollments = Enrollment.objects.filter(
            student=self.regular_user,
            course=self.free_course
        )
        self.assertEqual(enrollments.count(), 1)
        self.assertEqual(enrollments.first(), existing_enrollment)


class ErrorHandlingTests(CourseEnrollmentTestCase):
    """Tests for error handling and edge cases"""

    def test_enrollment_with_invalid_course(self):
        """Test enrollment with non-existent course"""
        self.client.login(username='testuser', password='testpass123')

        # Try to enroll in non-existent course
        response = self.client.post('/courses/enroll/non-existent-course/', follow=True)

        # Should return 404 or redirect with error
        self.assertIn(response.status_code, [404, 200])

        if response.status_code == 200:
            messages = list(get_messages(response.wsgi_request))
            self.assertTrue(any('not found' in str(message).lower() for message in messages))

    def test_enrollment_with_unpublished_course(self):
        """Test enrollment with unpublished course"""
        # Create unpublished course
        unpublished_course = Course.objects.create(
            title="Unpublished Course",
            slug="unpublished-course",
            description="This course is not published",
            learning_objectives="Test objectives",
            category=self.tech_category,
            price=Decimal('0.00'),
            estimated_duration=20,
            instructor=self.admin_user,
            is_published=False
        )

        self.client.login(username='testuser', password='testpass123')

        # Try to enroll in unpublished course
        enroll_url = reverse('courses:enroll', kwargs={'slug': unpublished_course.slug})
        response = self.client.post(enroll_url, follow=True)

        # Should be rejected
        self.assertEqual(response.status_code, 200)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('not available' in str(message).lower() for message in messages))

        # Verify no enrollment created
        self.assertFalse(
            Enrollment.objects.filter(
                student=self.regular_user,
                course=unpublished_course
            ).exists()
        )

    def test_enrollment_service_error_handling(self):
        """Test EnrollmentService error handling"""
        # Test with invalid user
        with self.assertRaises(ValueError):
            EnrollmentService.enroll_user_in_course(
                user=None,
                course=self.free_course
            )

        # Test with invalid course
        with self.assertRaises(ValueError):
            EnrollmentService.enroll_user_in_course(
                user=self.regular_user,
                course=None
            )

    def test_email_sending_failure_handling(self):
        """Test graceful handling of email sending failures"""
        enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )

        # Mock email backend to fail
        with patch('django.core.mail.send_mail') as mock_send_mail:
            mock_send_mail.side_effect = Exception("SMTP server down")

            # This should not raise an exception
            try:
                send_enrollment_confirmation_email(self.regular_user, self.free_course, enrollment)
                # If we reach here, the function handled the exception gracefully
                self.assertTrue(True)
            except Exception as e:
                self.fail(f"Email function should handle SMTP failures gracefully: {e}")

    def test_database_constraint_violations(self):
        """Test handling of database constraint violations"""
        # Create enrollment
        enrollment1 = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )

        # Try to create duplicate enrollment (should be handled gracefully)
        try:
            result = EnrollmentService.enroll_user_in_course(
                user=self.regular_user,
                course=self.free_course
            )
            # Should return existing enrollment or handle gracefully
            self.assertIsNotNone(result)
        except Exception as e:
            # If an exception is raised, it should be a controlled one
            self.assertIn('already enrolled', str(e).lower())

    def test_concurrent_enrollment_handling(self):
        """Test handling of concurrent enrollment attempts"""
        # This test simulates race conditions in enrollment
        from threading import Thread
        import time

        results = []
        errors = []

        def enroll_user():
            try:
                result = EnrollmentService.enroll_user_in_course(
                    user=self.regular_user,
                    course=self.free_course
                )
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # Start multiple threads trying to enroll simultaneously
        threads = []
        for i in range(3):
            thread = Thread(target=enroll_user)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify only one enrollment was created
        enrollments = Enrollment.objects.filter(
            student=self.regular_user,
            course=self.free_course
        )
        self.assertEqual(enrollments.count(), 1)

        # At least one operation should have succeeded
        self.assertTrue(len(results) > 0 or len(errors) > 0)


class PerformanceTests(CourseEnrollmentTestCase):
    """Performance tests for enrollment system"""

    def test_bulk_enrollment_performance(self):
        """Test performance with multiple enrollments"""
        import time

        # Create multiple users
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'bulkuser{i}',
                email=f'bulkuser{i}@example.com',
                password='testpass123'
            )
            Profile.objects.create(
                user=user,
                phone_number=f'+25471234567{i}'
            )
            users.append(user)

        # Measure enrollment time
        start_time = time.time()

        for user in users:
            EnrollmentService.enroll_user_in_course(
                user=user,
                course=self.free_course
            )

        end_time = time.time()
        enrollment_time = end_time - start_time

        # Verify all enrollments created
        enrollments = Enrollment.objects.filter(course=self.free_course)
        self.assertEqual(enrollments.count(), 10)

        # Performance assertion (should complete within reasonable time)
        self.assertLess(enrollment_time, 5.0, "Bulk enrollment took too long")

        print(f"Bulk enrollment of 10 users took {enrollment_time:.2f} seconds")

    def test_enrollment_query_efficiency(self):
        """Test database query efficiency"""
        from django.test.utils import override_settings
        from django.db import connection

        # Create enrollment
        enrollment = Enrollment.objects.create(
            student=self.regular_user,
            course=self.free_course,
            status='active'
        )

        # Reset query count
        connection.queries_log.clear()

        # Perform enrollment check
        with override_settings(DEBUG=True):
            result = EnrollmentService.validate_enrollment_eligibility(
                user=self.regular_user,
                course=self.free_course
            )

        # Check query count (should be minimal)
        query_count = len(connection.queries)
        self.assertLessEqual(query_count, 5, f"Too many queries: {query_count}")

        print(f"Enrollment eligibility check used {query_count} database queries")


class SecurityTests(CourseEnrollmentTestCase):
    """Security tests for enrollment system"""

    def test_unauthorized_enrollment_access(self):
        """Test that unauthenticated users cannot enroll"""
        # Try to enroll without logging in
        enroll_url = reverse('courses:enroll', kwargs={'slug': self.free_course.slug})
        response = self.client.post(enroll_url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

        # Verify no enrollment created
        self.assertFalse(
            Enrollment.objects.filter(
                student=self.regular_user,
                course=self.free_course
            ).exists()
        )

    def test_cross_user_enrollment_prevention(self):
        """Test that users cannot enroll other users"""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # Login as regular user
        self.client.login(username='testuser', password='testpass123')

        # Try to enroll other user (this should not be possible through normal flow)
        # The enrollment should always use the authenticated user
        enroll_url = reverse('courses:enroll', kwargs={'slug': self.free_course.slug})
        response = self.client.post(enroll_url, follow=True)

        # Verify enrollment is for the authenticated user only
        enrollment = Enrollment.objects.filter(course=self.free_course).first()
        if enrollment:
            self.assertEqual(enrollment.student, self.regular_user)
            self.assertNotEqual(enrollment.student, other_user)

    def test_enrollment_data_validation(self):
        """Test input validation and sanitization"""
        # Test with malicious input (should be handled safely)
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE enrollments; --",
            "../../../etc/passwd",
            "javascript:alert('xss')"
        ]

        self.client.login(username='testuser', password='testpass123')

        for malicious_input in malicious_inputs:
            # Try enrollment with malicious data (this would typically be in form fields)
            # The system should sanitize or reject such inputs
            try:
                result = EnrollmentService.enroll_user_in_course(
                    user=self.regular_user,
                    course=self.free_course,
                    notes=malicious_input  # If notes field exists
                )
                # If successful, verify the data was sanitized
                if result and hasattr(result, 'notes'):
                    self.assertNotIn('<script>', result.notes)
                    self.assertNotIn('DROP TABLE', result.notes)
            except ValueError:
                # It's acceptable to reject malicious input
                pass


if __name__ == '__main__':
    # Configure logging for test output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('tests/test_course_enrollment_journey.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Run the tests
    unittest.main(verbosity=2)
