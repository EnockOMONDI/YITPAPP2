#!/usr/bin/env python3
"""
YITP Payment Integration Test Suite
==================================

Comprehensive test suite for payment processing integration including
M-Pesa API mocking, payment status tracking, and error handling.

Test Coverage:
1. M-Pesa STK Push Integration
2. Payment Callback Processing
3. Payment Status Verification
4. Bank Transfer Processing
5. Payment Timeout Handling
6. Error Recovery Scenarios
7. Payment Security Validation
8. Admin Notification System

Author: YITP Development Team
Date: 2025-01-05
"""

import os
import sys
import django
import unittest
import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, Mock, MagicMock

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from users.models import Profile
from courses.models import Course, Category

# Import payment modules if available
try:
    from payments.models import Payment, PaymentMethod, PaymentCallback
    from payments.payment_service import PaymentService
    PAYMENTS_AVAILABLE = True
except ImportError:
    PAYMENTS_AVAILABLE = False


@unittest.skipUnless(PAYMENTS_AVAILABLE, "Payment modules not available")
class PaymentIntegrationTests(TestCase):
    """Integration tests for payment processing workflows"""
    
    def setUp(self):
        """Set up test data for payment integration tests"""
        # Create test category and course
        self.category = Category.objects.create(
            name="Technology",
            slug="technology",
            description="Technology courses"
        )
        
        self.course = Course.objects.create(
            title="Advanced Web Development",
            slug="advanced-web-development",
            description="Master modern web development",
            category=self.category,
            price=Decimal('15000.00'),
            duration_weeks=12,
            is_published=True
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='+254712345678',
            payment_status='unpaid'
        )
        
        # Create payment methods
        self.mpesa_method = PaymentMethod.objects.create(
            code='mpesa',
            name='M-Pesa',
            description='Pay using M-Pesa mobile money',
            enabled=True,
            requires_phone=True
        )
        
        self.bank_method = PaymentMethod.objects.create(
            code='bank_transfer',
            name='Bank Transfer',
            description='Direct bank transfer',
            enabled=True,
            requires_phone=False
        )
        
        self.client = Client()
    
    @patch('payments.payment_service.requests.post')
    def test_mpesa_stk_push_success_flow(self, mock_post):
        """Test complete M-Pesa STK push success flow"""
        # Mock successful M-Pesa auth response
        auth_response = Mock()
        auth_response.status_code = 200
        auth_response.json.return_value = {
            'access_token': 'test_access_token_123',
            'expires_in': '3599'
        }
        
        # Mock successful STK push response
        stk_response = Mock()
        stk_response.status_code = 200
        stk_response.json.return_value = {
            'ResponseCode': '0',
            'ResponseDescription': 'Success. Request accepted for processing',
            'MerchantRequestID': 'test-merchant-123',
            'CheckoutRequestID': 'test-checkout-456'
        }
        
        mock_post.side_effect = [auth_response, stk_response]
        
        # Create payment record
        payment = Payment.objects.create(
            user=self.user,
            payment_method=self.mpesa_method,
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            status='pending',
            course=self.course
        )
        
        # Process M-Pesa payment
        result = PaymentService.process_mpesa_payment(payment)
        
        # Verify success
        self.assertTrue(result['success'])
        self.assertEqual(result['merchant_request_id'], 'test-merchant-123')
        self.assertEqual(result['checkout_request_id'], 'test-checkout-456')
        
        # Verify payment updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'processing')
        self.assertEqual(payment.merchant_request_id, 'test-merchant-123')
        self.assertEqual(payment.checkout_request_id, 'test-checkout-456')
        
        # Verify API calls
        self.assertEqual(mock_post.call_count, 2)
        
        # Verify auth call
        auth_call = mock_post.call_args_list[0]
        self.assertIn('oauth/v1/generate', auth_call[1]['url'])
        
        # Verify STK push call
        stk_call = mock_post.call_args_list[1]
        self.assertIn('stkpush/v1/processrequest', stk_call[1]['url'])
        
        stk_data = json.loads(stk_call[1]['data'])
        self.assertEqual(stk_data['Amount'], '15000')
        self.assertEqual(stk_data['PhoneNumber'], '254712345678')
    
    def test_mpesa_callback_success_processing(self):
        """Test successful M-Pesa callback processing"""
        # Create payment in processing state
        payment = Payment.objects.create(
            user=self.user,
            payment_method=self.mpesa_method,
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            status='processing',
            checkout_request_id='test-checkout-456',
            course=self.course
        )
        
        # Simulate successful callback data
        callback_data = {
            'CheckoutRequestID': 'test-checkout-456',
            'ResultCode': 0,
            'ResultDesc': 'The service request is processed successfully.',
            'MpesaReceiptNumber': 'MPE123456789',
            'Amount': 15000.00,
            'TransactionDate': '20250105143022'
        }
        
        # Process callback
        result = PaymentService.confirm_payment(payment, callback_data)
        
        # Verify success
        self.assertTrue(result['success'])
        
        # Verify payment status updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'confirmed')
        self.assertEqual(payment.mpesa_receipt_number, 'MPE123456789')
        self.assertIsNotNone(payment.confirmed_at)
        
        # Verify user profile updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.payment_status, 'confirmed')
        self.assertEqual(self.profile.payment_amount, Decimal('15000.00'))
        self.assertIsNotNone(self.profile.payment_confirmed_at)
        self.assertEqual(self.profile.payment_reference, payment.reference_number)
    
    def test_mpesa_callback_failure_processing(self):
        """Test M-Pesa callback failure processing"""
        # Create payment in processing state
        payment = Payment.objects.create(
            user=self.user,
            payment_method=self.mpesa_method,
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            status='processing',
            checkout_request_id='test-checkout-456',
            course=self.course
        )
        
        # Simulate failed callback data
        callback_data = {
            'CheckoutRequestID': 'test-checkout-456',
            'ResultCode': 1032,
            'ResultDesc': 'Request cancelled by user'
        }
        
        # Process callback
        result = PaymentService.confirm_payment(payment, callback_data)
        
        # Verify failure handling
        self.assertFalse(result['success'])
        self.assertIn('cancelled by user', result['error'])
        
        # Verify payment status updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')
        self.assertEqual(payment.failure_reason, 'Request cancelled by user')
        
        # Verify user profile not updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.payment_status, 'unpaid')
    
    def test_bank_transfer_processing(self):
        """Test bank transfer payment processing"""
        # Create bank transfer payment
        payment = Payment.objects.create(
            user=self.user,
            payment_method=self.bank_method,
            amount=Decimal('15000.00'),
            status='pending',
            bank_reference='BT-2025-001',
            course=self.course
        )
        
        # Simulate admin confirmation
        confirmation_data = {
            'confirmed_by': 'admin@yitp.com',
            'confirmation_notes': 'Bank transfer verified via statement',
            'bank_transaction_id': 'ABSA-TXN-789'
        }
        
        result = PaymentService.confirm_bank_transfer(payment, confirmation_data)
        
        # Verify success
        self.assertTrue(result['success'])
        
        # Verify payment updated
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'confirmed')
        self.assertEqual(payment.bank_transaction_id, 'ABSA-TXN-789')
        self.assertIsNotNone(payment.confirmed_at)
        
        # Verify user profile updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.payment_status, 'confirmed')
    
    def test_payment_timeout_handling(self):
        """Test payment timeout handling"""
        # Create payment that should timeout
        old_time = timezone.now() - timedelta(hours=25)  # 25 hours ago
        
        payment = Payment.objects.create(
            user=self.user,
            payment_method=self.mpesa_method,
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            status='processing',
            checkout_request_id='test-checkout-456',
            course=self.course
        )
        
        # Manually set old creation time
        payment.created_at = old_time
        payment.save()
        
        # Run timeout check
        expired_payments = PaymentService.check_expired_payments()
        
        # Verify payment was marked as expired
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'expired')
        self.assertIn(payment, expired_payments)
    
    def test_payment_security_validation(self):
        """Test payment security validation"""
        # Test amount validation
        with self.assertRaises(ValueError):
            PaymentService.create_payment_record(
                user=self.user,
                payment_method=self.mpesa_method,
                amount=Decimal('-100.00'),  # Negative amount
                phone_number='+254712345678'
            )
        
        # Test phone number validation for M-Pesa
        with self.assertRaises(ValueError):
            PaymentService.create_payment_record(
                user=self.user,
                payment_method=self.mpesa_method,
                amount=Decimal('15000.00'),
                phone_number='invalid-phone'  # Invalid phone
            )
        
        # Test maximum amount validation
        with self.assertRaises(ValueError):
            PaymentService.create_payment_record(
                user=self.user,
                payment_method=self.mpesa_method,
                amount=Decimal('1000000.00'),  # Amount too high
                phone_number='+254712345678'
            )
    
    def test_payment_callback_security(self):
        """Test payment callback security validation"""
        # Create payment
        payment = Payment.objects.create(
            user=self.user,
            payment_method=self.mpesa_method,
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            status='processing',
            checkout_request_id='test-checkout-456',
            course=self.course
        )
        
        # Test callback with wrong checkout request ID
        wrong_callback_data = {
            'CheckoutRequestID': 'wrong-checkout-id',
            'ResultCode': 0,
            'ResultDesc': 'Success',
            'MpesaReceiptNumber': 'MPE123456789'
        }
        
        result = PaymentService.confirm_payment(payment, wrong_callback_data)
        
        # Verify security check failed
        self.assertFalse(result['success'])
        self.assertIn('Invalid checkout request ID', result['error'])
        
        # Verify payment status unchanged
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'processing')
    
    def test_duplicate_payment_prevention(self):
        """Test prevention of duplicate payments"""
        # Create first payment
        payment1 = Payment.objects.create(
            user=self.user,
            payment_method=self.mpesa_method,
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            status='confirmed',
            course=self.course
        )
        
        # Try to create duplicate payment
        with self.assertRaises(ValueError):
            PaymentService.create_payment_record(
                user=self.user,
                payment_method=self.mpesa_method,
                amount=Decimal('15000.00'),
                phone_number='+254712345678',
                course_id=self.course.id
            )
    
    def test_payment_notification_emails(self):
        """Test payment notification emails"""
        # Create confirmed payment
        payment = Payment.objects.create(
            user=self.user,
            payment_method=self.mpesa_method,
            amount=Decimal('15000.00'),
            phone_number='+254712345678',
            status='confirmed',
            mpesa_receipt_number='MPE123456789',
            course=self.course
        )
        
        # Clear email outbox
        mail.outbox = []
        
        # Send payment confirmation email
        PaymentService.send_payment_confirmation_email(payment)
        
        # Verify email sent
        self.assertEqual(len(mail.outbox), 2)  # User + admin emails
        
        # Check user email
        user_email = next((email for email in mail.outbox if self.user.email in email.to), None)
        self.assertIsNotNone(user_email)
        self.assertIn('Payment Confirmed', user_email.subject)
        self.assertIn('MPE123456789', user_email.body)
        self.assertIn('KES 15,000', user_email.body)
        
        # Check admin email
        admin_email = next((email for email in mail.outbox if settings.ADMIN_EMAIL in email.to), None)
        self.assertIsNotNone(admin_email)
        self.assertIn('Payment Received', admin_email.subject)


@unittest.skipUnless(PAYMENTS_AVAILABLE, "Payment modules not available")
class PaymentViewTests(TestCase):
    """Tests for payment-related views"""
    
    def setUp(self):
        """Set up test data for payment view tests"""
        # Create test data (similar to above)
        self.category = Category.objects.create(
            name="Technology",
            slug="technology"
        )
        
        self.course = Course.objects.create(
            title="Test Course",
            slug="test-course",
            category=self.category,
            price=Decimal('10000.00'),
            is_published=True
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='+254712345678'
        )
        
        self.client = Client()
    
    def test_payment_methods_page_access(self):
        """Test access to payment methods page"""
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('payments:payment_methods')
        response = self.client.get(url, {'course': self.course.slug})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Choose Payment Method')
        self.assertContains(response, self.course.title)
        self.assertContains(response, 'KES 10,000')
    
    def test_payment_methods_page_unauthenticated(self):
        """Test payment methods page requires authentication"""
        url = reverse('payments:payment_methods')
        response = self.client.get(url, {'course': self.course.slug})
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    @patch('payments.payment_service.PaymentService.process_mpesa_payment')
    def test_mpesa_payment_processing_view(self, mock_process):
        """Test M-Pesa payment processing view"""
        self.client.login(username='testuser', password='testpass123')
        
        # Mock successful processing
        mock_process.return_value = {
            'success': True,
            'merchant_request_id': 'test-123',
            'checkout_request_id': 'test-456'
        }
        
        url = reverse('payments:process_mpesa')
        data = {
            'course_id': self.course.id,
            'amount': '10000.00',
            'phone_number': '+254712345678'
        }
        
        response = self.client.post(url, data, follow=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify payment record created
        payment = Payment.objects.filter(user=self.user, course=self.course).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, Decimal('10000.00'))
        self.assertEqual(payment.phone_number, '+254712345678')


if __name__ == '__main__':
    unittest.main(verbosity=2)
