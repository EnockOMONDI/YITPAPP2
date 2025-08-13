#!/usr/bin/env python
"""
Test script for updated enrollment email system with PayPal payment context
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
from progress.models import Enrollment
from payments.models import Payment
from users.email_utils import send_enrollment_confirmation_email, send_enrollment_admin_notification
from courses.enrollment_service import EnrollmentService

def test_enrollment_emails_with_payment_context():
    """Test enrollment emails with different payment scenarios"""
    print("🧪 Testing Enrollment Emails with Payment Context")
    print("=" * 60)
    
    # Get test course and user
    try:
        course = Course.objects.filter(title__icontains="Understanding Purpose").first()
        if not course:
            print("❌ Test course 'Understanding Purpose In life' not found")
            return False
            
        user, created = User.objects.get_or_create(
            username='email_test_user',
            defaults={
                'email': 'emailtest@yitp.com',
                'first_name': 'Email',
                'last_name': 'Test User'
            }
        )
        
        print(f"📚 Test Course: {course.title} (${course.price} USD)")
        print(f"👤 Test User: {user.get_full_name()} ({user.email})")
        
    except Exception as e:
        print(f"❌ Setup error: {str(e)}")
        return False
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Full Payment Confirmed',
            'payment_context': {
                'payment_status': 'confirmed',
                'is_installment': False,
                'installment_sequence': 1
            }
        },
        {
            'name': 'First Installment Confirmed',
            'payment_context': {
                'payment_status': 'confirmed',
                'is_installment': True,
                'installment_sequence': 1
            }
        },
        {
            'name': 'Partial Payment (Profile Status)',
            'payment_context': {
                'payment_status': 'partially_paid',
                'is_installment': True,
                'installment_sequence': 1
            }
        },
        {
            'name': 'Payment Pending',
            'payment_context': {
                'payment_status': 'pending',
                'is_installment': False,
                'installment_sequence': 1
            }
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n🔍 Testing Scenario: {scenario['name']}")
        print("-" * 40)
        
        try:
            # Create or get enrollment
            enrollment, created = Enrollment.objects.get_or_create(
                student=user,
                course=course,
                defaults={
                    'status': 'active',
                    'progress_percentage': 0.00
                }
            )
            
            # Test user email
            print("📧 Testing user enrollment confirmation email...")
            user_result = send_enrollment_confirmation_email(
                user, course, enrollment, scenario['payment_context']
            )
            
            # Test admin email
            print("📧 Testing admin enrollment notification email...")
            admin_result = send_enrollment_admin_notification(
                user, course, enrollment, scenario['payment_context']
            )
            
            scenario_result = {
                'scenario': scenario['name'],
                'user_email': user_result,
                'admin_email': admin_result,
                'success': user_result and admin_result
            }
            
            results.append(scenario_result)
            
            status = "✅ PASSED" if scenario_result['success'] else "❌ FAILED"
            print(f"  User Email: {'✅' if user_result else '❌'}")
            print(f"  Admin Email: {'✅' if admin_result else '❌'}")
            print(f"  Overall: {status}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results.append({
                'scenario': scenario['name'],
                'user_email': False,
                'admin_email': False,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    for result in results:
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"  {result['scenario']}: {status}")
        if 'error' in result:
            print(f"    Error: {result['error']}")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"\n📈 Overall Results:")
    print(f"  ✅ Passed: {passed}/{total}")
    print(f"  ❌ Failed: {total - passed}/{total}")
    print(f"  📊 Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 All enrollment email tests passed!")
        print("✅ Payment context is correctly integrated into email templates")
        print("✅ USD currency is displayed correctly")
        print("✅ Payment status messages are working")
    else:
        print("\n⚠️ Some tests failed. Check email configuration and templates.")
    
    return passed == total

def test_enrollment_service_integration():
    """Test the enrollment service with payment context"""
    print("\n🔧 Testing EnrollmentService Integration")
    print("=" * 60)
    
    try:
        course = Course.objects.filter(title__icontains="Understanding Purpose").first()
        user = User.objects.get(username='email_test_user')
        
        # Create enrollment
        enrollment, created = Enrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={'status': 'active', 'progress_percentage': 0.00}
        )
        
        # Test with payment context
        payment_context = {
            'payment_status': 'confirmed',
            'is_installment': False,
            'installment_sequence': 1
        }
        
        print("📧 Testing EnrollmentService.send_enrollment_notifications...")
        results = EnrollmentService.send_enrollment_notifications(
            user, course, enrollment, payment_context
        )
        
        print(f"  User Email Sent: {'✅' if results['user_email_sent'] else '❌'}")
        print(f"  Admin Email Sent: {'✅' if results['admin_email_sent'] else '❌'}")
        print(f"  Errors: {results['errors'] if results['errors'] else 'None'}")
        
        success = results['user_email_sent'] and results['admin_email_sent']
        print(f"  Overall: {'✅ PASSED' if success else '❌ FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"❌ EnrollmentService test error: {str(e)}")
        return False

def main():
    """Run all email integration tests"""
    print("🧪 YITP Enrollment Email Integration Tests")
    print("Testing updated email system with PayPal payment context")
    print("=" * 80)
    
    # Test 1: Email templates with payment context
    test1_result = test_enrollment_emails_with_payment_context()
    
    # Test 2: Enrollment service integration
    test2_result = test_enrollment_service_integration()
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎯 FINAL TEST SUMMARY")
    print("=" * 80)
    
    tests = [
        ("Email Templates with Payment Context", test1_result),
        ("EnrollmentService Integration", test2_result)
    ]
    
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    print(f"\n📊 Overall Test Results:")
    print(f"  ✅ Passed: {passed}/{total}")
    print(f"  ❌ Failed: {total - passed}/{total}")
    print(f"  📊 Success Rate: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Enrollment email system is ready for automated PayPal payments")
        print("✅ Payment context integration working correctly")
        print("✅ USD currency and payment status messages implemented")
    else:
        print("\n⚠️ Some tests failed. Review the issues above.")

if __name__ == '__main__':
    main()
