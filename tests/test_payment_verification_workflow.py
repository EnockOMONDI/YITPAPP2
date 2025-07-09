"""
Test Suite for Enhanced Payment Verification Workflow
Tests the complete PayPal and bank transfer verification process with email notifications
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core import mail
from decimal import Decimal
from unittest.mock import patch, MagicMock

from courses.models import Course
from progress.models import Enrollment
from payments.models import Payment
from payments.payment_service import PaymentService
from payments.email_service import PaymentEmailService
from users.models import Profile


class PaymentVerificationWorkflowTestCase(TestCase):
    """Test complete payment verification workflow with email notifications"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Get or update user profile (created automatically by signal)
        self.profile = self.user.profile
        self.profile.phone_number = '+254700000000'
        self.profile.payment_status = 'unpaid'
        self.profile.save()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create test course
        self.course = Course.objects.create(
            title='Test Course',
            description='Test course description',
            learning_objectives='Test learning objectives',
            estimated_duration=40,
            price=Decimal('5000.00'),
            instructor=self.admin_user
        )
        
        # Create client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_paypal_payment_validation_comprehensive(self):
        """Test comprehensive PayPal payment validation"""
        url = reverse('payments:process_paypal')
        
        # Test cases for validation
        test_cases = [
            {
                'paypal_payment_id': '',
                'expected_error': 'PayPal transaction ID is required'
            },
            {
                'paypal_payment_id': 'SHORT',
                'expected_error': 'minimum 10 characters'
            },
            {
                'paypal_payment_id': 'A' * 51,  # Too long
                'expected_error': 'too long'
            },
            {
                'paypal_payment_id': 'INVALID@#$%',
                'expected_error': 'invalid characters'
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(paypal_id=test_case['paypal_payment_id']):
                data = {
                    'course_id': self.course.id,
                    'amount': str(self.course.price),
                    'paypal_payment_id': test_case['paypal_payment_id'],
                    'is_installment': 'false'
                }
                
                response = self.client.post(url, data)
                
                # Should redirect back to payment methods
                self.assertRedirects(response, reverse('payments:payment_methods', args=[self.course.id]))
                
                # Check error message
                messages = list(get_messages(response.wsgi_request))
                self.assertTrue(any(test_case['expected_error'] in str(m) for m in messages))
    
    def test_bank_transfer_validation_comprehensive(self):
        """Test comprehensive bank transfer validation"""
        url = reverse('payments:process_bank_transfer')
        
        test_cases = [
            {
                'transaction_id': '',
                'expected_error': 'Bank transaction ID is required'
            },
            {
                'transaction_id': 'SHORT',
                'expected_error': 'minimum 8 characters'
            },
            {
                'transaction_id': 'A' * 51,  # Too long
                'expected_error': 'too long'
            },
            {
                'transaction_id': 'INVALID@#$%',
                'expected_error': 'invalid characters'
            }
        ]
        
        for test_case in test_cases:
            with self.subTest(transaction_id=test_case['transaction_id']):
                data = {
                    'course_id': self.course.id,
                    'amount': str(self.course.price),
                    'transaction_id': test_case['transaction_id'],
                    'is_installment': 'false'
                }
                
                response = self.client.post(url, data)
                
                # Should redirect back to payment methods
                self.assertRedirects(response, reverse('payments:payment_methods', args=[self.course.id]))
                
                # Check error message
                messages = list(get_messages(response.wsgi_request))
                self.assertTrue(any(test_case['expected_error'] in str(m) for m in messages))
    
    def test_paypal_payment_with_email_notifications(self):
        """Test PayPal payment submission with email notifications"""
        url = reverse('payments:process_paypal')
        
        # Clear any existing emails
        mail.outbox = []
        
        data = {
            'course_id': self.course.id,
            'amount': str(self.course.price),
            'paypal_payment_id': 'PAYPAL123456789',
            'paypal_payer_id': 'PAYER123456789',
            'is_installment': 'false'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to payment status
        payment = Payment.objects.filter(
            user=self.user,
            course=self.course,
            payment_method='paypal'
        ).first()
        
        self.assertIsNotNone(payment)
        self.assertRedirects(response, reverse('payments:payment_status', args=[payment.id]))
        
        # Check payment details
        self.assertEqual(payment.paypal_payment_id, 'PAYPAL123456789')
        self.assertEqual(payment.paypal_payer_id, 'PAYER123456789')
        self.assertEqual(payment.status, 'pending')
        
        # Check emails were sent (2 emails: user confirmation + admin notification)
        self.assertEqual(len(mail.outbox), 2)
        
        # Check user confirmation email
        user_email = next((email for email in mail.outbox if self.user.email in email.to), None)
        self.assertIsNotNone(user_email)
        self.assertIn('Payment Submitted Successfully', user_email.subject)
        self.assertIn('PAYPAL123456789', user_email.body)
        
        # Check admin notification email
        admin_email = next((email for email in mail.outbox if 'youthimpactglobal3@gmail.com' in email.to), None)
        self.assertIsNotNone(admin_email)
        self.assertIn('Payment Verification Required', admin_email.subject)
        self.assertIn('PAYPAL123456789', admin_email.body)
    
    def test_bank_transfer_payment_with_email_notifications(self):
        """Test bank transfer payment submission with email notifications"""
        url = reverse('payments:process_bank_transfer')
        
        # Clear any existing emails
        mail.outbox = []
        
        data = {
            'course_id': self.course.id,
            'amount': str(self.course.price),
            'transaction_id': 'BANK123456789',
            'is_installment': 'false'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to payment status
        payment = Payment.objects.filter(
            user=self.user,
            course=self.course,
            payment_method='bank_transfer'
        ).first()
        
        self.assertIsNotNone(payment)
        self.assertRedirects(response, reverse('payments:payment_status', args=[payment.id]))
        
        # Check payment details
        self.assertEqual(payment.transaction_id, 'BANK123456789')
        self.assertEqual(payment.status, 'pending')
        
        # Check emails were sent
        self.assertEqual(len(mail.outbox), 2)
        
        # Check user confirmation email
        user_email = next((email for email in mail.outbox if self.user.email in email.to), None)
        self.assertIsNotNone(user_email)
        self.assertIn('Payment Submitted Successfully', user_email.subject)
        
        # Check admin notification email
        admin_email = next((email for email in mail.outbox if 'youthimpactglobal3@gmail.com' in email.to), None)
        self.assertIsNotNone(admin_email)
        self.assertIn('Payment Verification Required', admin_email.subject)
    
    def test_duplicate_payment_prevention(self):
        """Test enhanced duplicate payment prevention"""
        # Create first PayPal payment
        first_payment = PaymentService.create_payment_record(
            user=self.user,
            course=self.course,
            amount=self.course.price,
            payment_method='paypal'
        )
        first_payment.paypal_payment_id = 'PAYPAL123456789'
        first_payment.save()
        
        url = reverse('payments:process_paypal')
        
        # Try to create duplicate with same transaction ID
        data = {
            'course_id': self.course.id,
            'amount': str(self.course.price),
            'paypal_payment_id': 'PAYPAL123456789',  # Same ID
            'is_installment': 'false'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect back to payment methods with error
        self.assertRedirects(response, reverse('payments:payment_methods', args=[self.course.id]))
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already been used' in str(m) for m in messages))
        
        # Should not create new payment
        payment_count = Payment.objects.filter(
            user=self.user,
            course=self.course,
            payment_method='paypal'
        ).count()
        self.assertEqual(payment_count, 1)
    
    def test_paypal_url_generation_error_handling(self):
        """Test PayPal URL generation with error handling"""
        # Test with valid payment
        payment = PaymentService.create_payment_record(
            user=self.user,
            course=self.course,
            amount=self.course.price,
            payment_method='paypal'
        )
        
        url = PaymentService._generate_paypal_url(payment)
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith('https://'))
        self.assertIn(payment.reference_number, url)
        
        # Test with invalid payment (None)
        fallback_url = PaymentService._generate_paypal_url(None)
        self.assertEqual(fallback_url, "https://www.paypal.com/ncp/payment/FUAJVJ66L978C")
    
    def test_email_service_error_handling(self):
        """Test email service error handling"""
        payment = PaymentService.create_payment_record(
            user=self.user,
            course=self.course,
            amount=self.course.price,
            payment_method='paypal'
        )
        
        # Test with valid payment
        result = PaymentEmailService.send_user_payment_submitted_notification(payment)
        self.assertTrue(result)
        
        # Test admin notification
        admin_result = PaymentEmailService.send_admin_verification_notification(payment)
        self.assertTrue(admin_result)
    
    def test_installment_payment_workflow(self):
        """Test installment payment workflow with notifications"""
        url = reverse('payments:process_paypal')
        
        # Clear emails
        mail.outbox = []
        
        # Submit first installment
        data = {
            'course_id': self.course.id,
            'amount': str(self.course.price * Decimal('0.5')),
            'paypal_payment_id': 'PAYPAL_INSTALL_1',
            'is_installment': 'true',
            'installment_sequence': '1'
        }
        
        response = self.client.post(url, data)
        
        payment = Payment.objects.filter(
            user=self.user,
            course=self.course,
            is_installment=True,
            installment_sequence=1
        ).first()
        
        self.assertIsNotNone(payment)
        self.assertTrue(payment.is_installment)
        self.assertEqual(payment.installment_sequence, 1)
        
        # Check emails were sent
        self.assertEqual(len(mail.outbox), 2)
        
        # Check installment information in emails
        user_email = next((email for email in mail.outbox if self.user.email in email.to), None)
        self.assertIn('Installment 1 of 2', user_email.body)


if __name__ == '__main__':
    import unittest
    unittest.main()
