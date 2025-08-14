#!/usr/bin/env python
"""
Investigate payment and enrollment status
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from payments.models import Payment
from progress.models import Enrollment
from django.contrib.auth.models import User

def investigate_payment_enrollment():
    """Investigate why payment doesn't have enrollment"""
    
    try:
        # Find the user and their payments
        user = User.objects.get(email='direso3598@jobzyy.com')
        payments = Payment.objects.filter(user=user).order_by('-created_at')
        
        print(f"User: {user.email}")
        print(f"User ID: {user.id}")
        
        # Check all enrollments for this user
        enrollments = Enrollment.objects.filter(student=user)
        print(f"\nTotal enrollments: {enrollments.count()}")
        
        for enrollment in enrollments:
            print(f"Enrollment ID: {enrollment.id}")
            print(f"Course: {enrollment.course.title}")
            print(f"Status: {enrollment.status}")
            print(f"Created: {enrollment.created_at}")
            print(f"Progress: {enrollment.progress_percentage}%")
            print("---")
        
        print(f"\nTotal payments: {payments.count()}")
        
        for payment in payments:
            print(f"\nPayment ID: {payment.id}")
            print(f"Reference: {payment.reference_number}")
            print(f"Course: {payment.course.title}")
            print(f"Status: {payment.status}")
            print(f"Amount: ${payment.amount}")
            print(f"Created: {payment.created_at}")
            print(f"Confirmed: {payment.confirmed_at}")
            
            # Check if there's an enrollment for this course
            try:
                enrollment = Enrollment.objects.get(student=user, course=payment.course)
                print(f"✅ Enrollment found: {enrollment.id}")
            except Enrollment.DoesNotExist:
                print(f"❌ No enrollment found for course: {payment.course.title}")
                
                # Try to create enrollment if payment is confirmed
                if payment.status == 'confirmed':
                    print(f"🔧 Creating missing enrollment for confirmed payment...")
                    
                    from courses.enrollment_service import EnrollmentService
                    
                    # Check if user has payment access via profile
                    profile = user.profile
                    has_access = profile.has_any_payment_access
                    print(f"Has payment access: {has_access}")
                    print(f"Profile payment status: {profile.payment_status}")
                    
                    if has_access:
                        # Create enrollment
                        enrollment, created = Enrollment.objects.get_or_create(
                            student=user,
                            course=payment.course,
                            defaults={
                                'status': 'active',
                                'progress_percentage': 0.00
                            }
                        )
                        
                        if created:
                            print(f"✅ Created enrollment: {enrollment.id}")
                            
                            # Send enrollment notifications
                            payment_context = {
                                'payment_status': 'confirmed',
                                'is_installment': payment.is_installment,
                                'installment_sequence': payment.installment_sequence or 1,
                            }
                            
                            try:
                                enrollment_result = EnrollmentService.send_enrollment_notifications(
                                    user, payment.course, enrollment, payment_context
                                )
                                print(f"Enrollment notifications: {enrollment_result}")
                            except Exception as e:
                                print(f"Failed to send enrollment notifications: {str(e)}")
                        else:
                            print(f"Enrollment already exists: {enrollment.id}")
            except Exception as e:
                print(f"Error checking enrollment: {str(e)}")
        
        # Check user profile payment status
        if hasattr(user, 'profile'):
            profile = user.profile
            print(f"\nUser Profile:")
            print(f"Payment Status: {profile.payment_status}")
            print(f"Payment Amount: {profile.payment_amount}")
            print(f"Payment Method: {profile.payment_method}")
            print(f"Payment Confirmed At: {profile.payment_confirmed_at}")
            print(f"Payment Expiration: {profile.payment_expiration_date}")
        
    except User.DoesNotExist:
        print("❌ User not found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    print("🔍 INVESTIGATING PAYMENT AND ENROLLMENT STATUS")
    print("=" * 60)
    investigate_payment_enrollment()
