#!/usr/bin/env python
"""
Fix missing email notifications for successful PayPal payments
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from payments.models import Payment
from payments.email_service import PaymentEmailService
from django.contrib.auth.models import User

def fix_missing_notifications():
    """Fix missing email notifications for confirmed payments"""
    
    try:
        # Find the user and their confirmed payment
        user = User.objects.get(email='direso3598@jobzyy.com')
        confirmed_payment = Payment.objects.get(id=15, user=user, status='confirmed')
        
        print(f"Found confirmed payment: {confirmed_payment.reference_number}")
        print(f"Amount: ${confirmed_payment.amount} {confirmed_payment.currency}")
        print(f"Transaction ID: {confirmed_payment.transaction_id}")
        print(f"Confirmed at: {confirmed_payment.confirmed_at}")
        
        # Send the missing success notification to user
        print("\nSending PayPal success notification to user...")
        user_result = PaymentEmailService.send_paypal_payment_success_notification(
            confirmed_payment,
            confirmed_payment.transaction_id
        )
        
        if user_result:
            print("✅ User notification sent successfully")
        else:
            print("❌ Failed to send user notification")
        
        # Send the missing admin notification
        print("\nSending PayPal admin notification...")
        admin_result = PaymentEmailService.send_paypal_admin_success_notification(
            confirmed_payment,
            confirmed_payment.transaction_id
        )
        
        if admin_result:
            print("✅ Admin notification sent successfully")
        else:
            print("❌ Failed to send admin notification")
        
        # Also send enrollment confirmation emails with payment context
        print("\nSending enrollment confirmation emails...")
        from courses.enrollment_service import EnrollmentService
        from progress.models import Enrollment
        
        # Find the enrollment for this payment
        try:
            enrollment = Enrollment.objects.get(student=user, course=confirmed_payment.course)
            
            payment_context = {
                'payment_status': 'confirmed',
                'is_installment': confirmed_payment.is_installment,
                'installment_sequence': confirmed_payment.installment_sequence or 1,
            }
            
            enrollment_result = EnrollmentService.send_enrollment_notifications(
                user, confirmed_payment.course, enrollment, payment_context
            )
            
            print(f"Enrollment notifications result: {enrollment_result}")
            
        except Enrollment.DoesNotExist:
            print("⚠️ No enrollment found for this payment")
        
        print(f"\n🎉 Notification fix completed for {user.email}")
        
    except User.DoesNotExist:
        print("❌ User not found")
    except Payment.DoesNotExist:
        print("❌ Payment not found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_email_system():
    """Test the email system to ensure it's working"""
    print("\n🧪 Testing email system...")
    
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Test basic email sending
        result = send_mail(
            subject='YITP Email System Test',
            message='This is a test email to verify the email system is working.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['youthimpactglobal3@gmail.com'],
            fail_silently=False
        )
        
        if result:
            print("✅ Email system is working")
        else:
            print("❌ Email system failed")
            
    except Exception as e:
        print(f"❌ Email system error: {str(e)}")

if __name__ == '__main__':
    print("🔧 FIXING MISSING PAYPAL NOTIFICATIONS")
    print("=" * 50)
    
    # Test email system first
    test_email_system()
    
    # Fix missing notifications
    fix_missing_notifications()
