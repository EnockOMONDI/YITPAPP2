"""
Test Suite for PayPal Integration in YITP Payment System
Tests PayPal payment processing, verification, and course enrollment
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.messages import get_messages
from decimal import Decimal

from courses.models import Course, Enrollment
from payments.models import Payment
from payments.payment_service import PaymentService
from users.models import Profile


class PayPalIntegrationTestCase(TestCase):
    """Test PayPal payment integration and workflow"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create user profile
        self.profile = Profile.objects.create(
            user=self.user,
            phone_number='+254700000000',
            payment_status='unpaid'
        )
        
        # Create test course
        self.course = Course.objects.create(
            title='Test Course',
            description='Test course description',
            price=Decimal('5000.00'),
            is_free=False
        )
        
        # Create client and login
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_paypal_payment_creation(self):
        """Test PayPal payment record creation"""
        payment = PaymentService.create_payment_record(
            user=self.user,
            course=self.course,
            amount=self.course.price,
            payment_method='paypal',
            is_installment=False
        )
        
        self.assertIsNotNone(payment)
        self.assertEqual(payment.payment_method, 'paypal')
        self.assertEqual(payment.amount, self.course.price)
        self.assertEqual(payment.status, 'pending')
        self.assertFalse(payment.is_installment)
    
    def test_paypal_installment_payment_creation(self):
        """Test PayPal installment payment creation"""
        payment = PaymentService.create_installment_payment(
            user=self.user,
            course=self.course,
            installment_sequence=1,
            payment_method='paypal'
        )
        
        self.assertIsNotNone(payment)
        self.assertEqual(payment.payment_method, 'paypal')
        self.assertEqual(payment.amount, self.course.price * Decimal('0.5'))
        self.assertTrue(payment.is_installment)
        self.assertEqual(payment.installment_sequence, 1)
    
    def test_paypal_payment_view_post(self):
        """Test PayPal payment processing view"""
        url = reverse('payments:process_paypal')
        
        data = {
            'course_id': self.course.id,
            'amount': str(self.course.price),
            'paypal_payment_id': 'PAYPAL123456789',
            'paypal_payer_id': 'PAYER123',
            'is_installment': 'false',
            'installment_sequence': '1'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to payment status
        self.assertEqual(response.status_code, 302)
        
        # Check payment was created
        payment = Payment.objects.filter(
            user=self.user,
            course=self.course,
            payment_method='paypal'
        ).first()
        
        self.assertIsNotNone(payment)
        self.assertEqual(payment.paypal_payment_id, 'PAYPAL123456789')
        self.assertEqual(payment.paypal_payer_id, 'PAYER123')
        self.assertEqual(payment.status, 'pending')
    
    def test_paypal_payment_validation(self):
        """Test PayPal payment ID validation"""
        url = reverse('payments:process_paypal')
        
        # Test with invalid PayPal ID (too short)
        data = {
            'course_id': self.course.id,
            'amount': str(self.course.price),
            'paypal_payment_id': 'SHORT',  # Too short
            'is_installment': 'false'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect back to payment methods
        self.assertRedirects(response, reverse('payments:payment_methods', args=[self.course.id]))
        
        # Check error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('valid PayPal transaction ID' in str(m) for m in messages))
    
    def test_duplicate_payment_prevention(self):
        """Test prevention of duplicate PayPal payments"""
        # Create first payment
        first_payment = PaymentService.create_payment_record(
            user=self.user,
            course=self.course,
            amount=self.course.price,
            payment_method='paypal'
        )
        
        url = reverse('payments:process_paypal')
        data = {
            'course_id': self.course.id,
            'amount': str(self.course.price),
            'paypal_payment_id': 'PAYPAL987654321',
            'is_installment': 'false'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to existing payment status
        self.assertRedirects(response, reverse('payments:payment_status', args=[first_payment.id]))
        
        # Should not create new payment
        payment_count = Payment.objects.filter(
            user=self.user,
            course=self.course,
            payment_method='paypal'
        ).count()
        self.assertEqual(payment_count, 1)
    
    def test_paypal_payment_confirmation_and_enrollment(self):
        """Test PayPal payment confirmation creates course enrollment"""
        # Create PayPal payment
        payment = PaymentService.create_payment_record(
            user=self.user,
            course=self.course,
            amount=self.course.price,
            payment_method='paypal'
        )
        payment.paypal_payment_id = 'PAYPAL123456789'
        payment.save()
        
        # Confirm payment and enroll
        result = PaymentService.confirm_payment_and_enroll(
            payment=payment,
            verified_by=None
        )
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['enrollment'])
        
        # Check payment status
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'confirmed')
        
        # Check enrollment created
        enrollment = Enrollment.objects.filter(
            student=self.user,
            course=self.course
        ).first()
        self.assertIsNotNone(enrollment)
        
        # Check profile updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.payment_status, 'confirmed')
    
    def test_paypal_installment_confirmation(self):
        """Test PayPal installment payment confirmation"""
        # Create first installment payment
        payment = PaymentService.create_installment_payment(
            user=self.user,
            course=self.course,
            installment_sequence=1,
            payment_method='paypal'
        )
        payment.paypal_payment_id = 'PAYPAL_INSTALL_1'
        payment.save()
        
        # Confirm first installment
        result = PaymentService.confirm_payment_and_enroll(
            payment=payment,
            verified_by=None
        )
        
        self.assertTrue(result['success'])
        
        # Check profile status for partial payment
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.payment_status, 'partially_paid')
        self.assertIsNotNone(self.profile.payment_expiry_date)
        
        # Check enrollment with partial payment status
        enrollment = result['enrollment']
        self.assertEqual(enrollment.payment_status, 'partially_paid')
    
    def test_payment_status_template_context(self):
        """Test payment status page displays PayPal information correctly"""
        # Create PayPal payment
        payment = PaymentService.create_payment_record(
            user=self.user,
            course=self.course,
            amount=self.course.price,
            payment_method='paypal'
        )
        payment.paypal_payment_id = 'PAYPAL123456789'
        payment.save()
        
        url = reverse('payments:payment_status', args=[payment.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PayPal Payment Verification')
        self.assertContains(response, 'PAYPAL123456789')
        self.assertContains(response, 'being verified by our team')
    
    def test_existing_enrollment_check(self):
        """Test PayPal payment prevents duplicate enrollment"""
        # Create existing enrollment
        Enrollment.objects.create(
            student=self.user,
            course=self.course
        )
        
        url = reverse('payments:process_paypal')
        data = {
            'course_id': self.course.id,
            'amount': str(self.course.price),
            'paypal_payment_id': 'PAYPAL123456789',
            'is_installment': 'false'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect to course detail
        self.assertRedirects(response, reverse('courses:course_detail', args=[self.course.id]))
        
        # Check message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already enrolled' in str(m) for m in messages))


if __name__ == '__main__':
    import unittest
    unittest.main()
