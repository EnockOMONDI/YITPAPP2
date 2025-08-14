#!/usr/bin/env python
"""
PayPal Integration Test Script for YITP
Tests the complete automated PayPal payment workflow
"""

import os
import sys
import django
from decimal import Decimal

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course
from payments.models import Payment
from payments.payment_service import PaymentService
from payments.paypal_service import PayPalService
from payments.email_service import PaymentEmailService

def test_paypal_configuration():
    """Test PayPal configuration and credentials"""
    print("🔧 Testing PayPal Configuration...")
    
    from django.conf import settings
    
    config_items = [
        ('PAYPAL_MODE', getattr(settings, 'PAYPAL_MODE', 'Not set')),
        ('PAYPAL_CLIENT_ID', getattr(settings, 'PAYPAL_CLIENT_ID', 'Not set')[:20] + '...'),
        ('PAYPAL_CLIENT_SECRET', 'Set' if getattr(settings, 'PAYPAL_CLIENT_SECRET', None) else 'Not set'),
        ('PAYPAL_WEBHOOK_ID', getattr(settings, 'PAYPAL_WEBHOOK_ID', 'Not set')),
        ('PAYPAL_BASE_URL', getattr(settings, 'PAYPAL_BASE_URL', 'Not set')),
        ('PAYPAL_WEBHOOK_URL', getattr(settings, 'PAYPAL_WEBHOOK_URL', 'Not set')),
    ]
    
    for key, value in config_items:
        status = '✅' if value != 'Not set' and value else '❌'
        print(f"  {status} {key}: {value}")
    
    return all(item[1] != 'Not set' and item[1] for item in config_items if item[0] != 'PAYPAL_WEBHOOK_ID')

def test_paypal_api_connection():
    """Test PayPal API connection"""
    print("\n🌐 Testing PayPal API Connection...")
    
    try:
        token_result = PayPalService.get_access_token()
        if token_result['success']:
            print("  ✅ PayPal API connection successful")
            print(f"  ✅ Access token obtained: {token_result['access_token'][:20]}...")
            return True
        else:
            print(f"  ❌ PayPal API connection failed: {token_result['message']}")
            return False
    except Exception as e:
        print(f"  ❌ PayPal API connection error: {str(e)}")
        return False

def test_payment_creation():
    """Test payment record creation"""
    print("\n💰 Testing Payment Creation...")
    
    try:
        # Get test course
        course = Course.objects.filter(is_published=True).first()
        if not course:
            print("  ❌ No published course found for testing")
            return False
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='paypal_test_user',
            defaults={
                'email': 'test@yitp.com',
                'first_name': 'PayPal',
                'last_name': 'Test User'
            }
        )
        
        print(f"  📚 Test Course: {course.title}")
        print(f"  👤 Test User: {user.get_full_name()} ({user.email})")
        
        # Create payment record
        payment = PaymentService.create_payment_record(
            user=user,
            course=course,
            amount=Decimal('2.00'),
            payment_method='paypal',
            is_installment=False,
            installment_sequence=1
        )
        
        print(f"  ✅ Payment record created: {payment.reference_number}")
        print(f"  ✅ Amount: ${payment.amount} USD")
        
        return payment
        
    except Exception as e:
        print(f"  ❌ Payment creation error: {str(e)}")
        return False

def test_paypal_order_creation(payment):
    """Test PayPal order creation"""
    print("\n🛒 Testing PayPal Order Creation...")
    
    try:
        result = PayPalService.create_payment_order(payment)
        
        if result['success']:
            print(f"  ✅ PayPal order created: {result['order_id']}")
            print(f"  ✅ Approval URL: {result['approval_url'][:50]}...")
            return result
        else:
            print(f"  ❌ PayPal order creation failed: {result['message']}")
            return False
            
    except Exception as e:
        print(f"  ❌ PayPal order creation error: {str(e)}")
        return False

def test_email_notifications(payment):
    """Test email notification system"""
    print("\n📧 Testing Email Notifications...")
    
    try:
        # Test payment initiated notification
        result1 = PaymentEmailService.send_paypal_payment_initiated_notification(payment)
        print(f"  {'✅' if result1 else '❌'} Payment initiated notification")
        
        # Test payment success notification
        result2 = PaymentEmailService.send_paypal_payment_success_notification(payment, 'TEST_TRANSACTION_ID')
        print(f"  {'✅' if result2 else '❌'} Payment success notification")
        
        # Test payment failure notification
        result3 = PaymentEmailService.send_paypal_payment_failed_notification(payment, 'Test error message')
        print(f"  {'✅' if result3 else '❌'} Payment failure notification")
        
        return result1 and result2 and result3
        
    except Exception as e:
        print(f"  ❌ Email notification error: {str(e)}")
        return False

def test_installment_payment():
    """Test installment payment creation"""
    print("\n📅 Testing Installment Payment...")
    
    try:
        # Get test course and user
        course = Course.objects.filter(is_published=True).first()
        user = User.objects.get(username='paypal_test_user')
        
        # Create installment payment
        installment_payment = PaymentService.create_payment_record(
            user=user,
            course=course,
            amount=course.price / 2,  # 50% for installment
            payment_method='paypal',
            is_installment=True,
            installment_sequence=1
        )
        
        print(f"  ✅ Installment payment created: {installment_payment.reference_number}")
        print(f"  ✅ Amount: ${installment_payment.amount} USD (50% of ${course.price})")
        print(f"  ✅ Installment sequence: {installment_payment.installment_sequence}")
        
        return installment_payment
        
    except Exception as e:
        print(f"  ❌ Installment payment error: {str(e)}")
        return False

def main():
    """Run all PayPal integration tests"""
    print("🧪 YITP PayPal Integration Test Suite")
    print("=" * 50)
    
    # Test results
    results = []
    
    # 1. Test configuration
    results.append(test_paypal_configuration())
    
    # 2. Test API connection
    results.append(test_paypal_api_connection())
    
    # 3. Test payment creation
    payment = test_payment_creation()
    results.append(bool(payment))
    
    if payment:
        # 4. Test PayPal order creation
        order_result = test_paypal_order_creation(payment)
        results.append(bool(order_result))
        
        # 5. Test email notifications
        results.append(test_email_notifications(payment))
        
        # 6. Test installment payment
        results.append(bool(test_installment_payment()))
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 Test Results Summary:")
    print(f"  ✅ Passed: {sum(results)}")
    print(f"  ❌ Failed: {len(results) - sum(results)}")
    print(f"  📊 Success Rate: {(sum(results)/len(results)*100):.1f}%")
    
    if all(results):
        print("\n🎉 All tests passed! PayPal integration is ready for testing.")
        print("\n📋 Next Steps:")
        print("  1. Update PayPal webhook ID in .env file")
        print("  2. Test payment flow on production site")
        print("  3. Verify email delivery")
        print("  4. Test with sandbox buyer account")
    else:
        print("\n⚠️ Some tests failed. Please review the configuration.")

if __name__ == '__main__':
    main()
