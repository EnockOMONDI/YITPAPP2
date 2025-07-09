#!/usr/bin/env python
"""
Test payment module imports and basic functionality
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/Users/djsean/Desktop/APPS2024/YITP2025/YITPAPP')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

def test_payment_integration():
    """Test payment integration functionality"""
    try:
        print("Testing payment integration functionality...")

        # Import required modules
        from django.contrib.auth.models import User
        from payments.models import Payment, PaymentMethod
        from payments.payment_service import PaymentService
        from courses.models import Course, Category
        from users.models import Profile
        from courses.enrollment_service import EnrollmentService
        from decimal import Decimal
        from django.utils import timezone

        print("✅ All modules imported successfully")

        # Test 1: Create test payment methods
        print("\n1. Creating test payment methods...")
        mpesa_method, created = PaymentMethod.objects.get_or_create(
            code='mpesa',
            defaults={
                'name': 'M-Pesa',
                'description': 'Pay using M-Pesa mobile money',
                'is_active': True,
                'requires_phone': True,
                'processing_fee_percentage': Decimal('0.00')
            }
        )
        print(f"   M-Pesa method: {'created' if created else 'exists'}")

        # Test 2: Create test users and course
        print("\n2. Creating test data...")

        # Create test users
        regular_user, created = User.objects.get_or_create(
            username='testuser_payment',
            defaults={
                'email': 'testuser@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )

        paid_user, created = User.objects.get_or_create(
            username='paiduser_payment',
            defaults={
                'email': 'paiduser@example.com',
                'first_name': 'Paid',
                'last_name': 'User'
            }
        )

        admin_user, created = User.objects.get_or_create(
            username='admin_payment',
            defaults={
                'email': 'admin@example.com',
                'is_superuser': True,
                'is_staff': True
            }
        )

        # Create test category and course
        category, created = Category.objects.get_or_create(
            slug="technology-test",
            defaults={
                'name': "Technology Test",
                'description': "Technology courses for testing"
            }
        )

        paid_course, created = Course.objects.get_or_create(
            slug="test-paid-course",
            defaults={
                'title': "Test Paid Course",
                'description': "Test course for payment integration",
                'learning_objectives': "Test payment workflow",
                'category': category,
                'price': Decimal('15000.00'),
                'estimated_duration': 40,
                'instructor': admin_user,
                'is_published': True,
                'enrollment_limit': 50
            }
        )

        print(f"   Test course created: {paid_course.title} (KES {paid_course.price})")

        # Test 3: Set up user profiles with payment status
        print("\n3. Setting up user payment profiles...")

        # Regular user - no payment
        regular_profile, created = Profile.objects.get_or_create(
            user=regular_user,
            defaults={
                'phone_number': '+254712345678',
                'payment_status': 'unpaid'
            }
        )
        regular_profile.payment_status = 'unpaid'
        regular_profile.save()

        # Paid user - confirmed payment
        paid_profile, created = Profile.objects.get_or_create(
            user=paid_user,
            defaults={
                'phone_number': '+254787654321',
                'payment_status': 'confirmed',
                'payment_confirmed_at': timezone.now(),
                'payment_amount': Decimal('15000.00'),
                'payment_reference': 'TEST-PAY-001'
            }
        )
        paid_profile.payment_status = 'confirmed'
        paid_profile.payment_confirmed_at = timezone.now()
        paid_profile.payment_amount = Decimal('15000.00')
        paid_profile.payment_reference = 'TEST-PAY-001'
        paid_profile.save()

        print(f"   Regular user payment status: {regular_profile.payment_status}")
        print(f"   Paid user payment status: {paid_profile.payment_status}")

        # Test 4: Test enrollment eligibility validation
        print("\n4. Testing enrollment eligibility validation...")

        # Test regular user (no payment) - should fail
        result1 = EnrollmentService.validate_enrollment_eligibility(regular_user, paid_course)
        print(f"   Regular user eligibility: {'✅ PASS' if not result1['is_valid'] else '❌ FAIL'}")
        if not result1['is_valid']:
            print(f"     Expected error: {result1.get('error_message', 'No error message')}")

        # Test paid user (confirmed payment) - should pass
        result2 = EnrollmentService.validate_enrollment_eligibility(paid_user, paid_course)
        print(f"   Paid user eligibility: {'✅ PASS' if result2['is_valid'] else '❌ FAIL'}")
        if not result2['is_valid']:
            print(f"     Unexpected error: {result2.get('error_message', 'No error message')}")

        # Test 5: Test enrollment workflow
        print("\n5. Testing enrollment workflow...")

        # Test enrollment failure for unpaid user
        result3 = EnrollmentService.enroll_user_in_course(regular_user, paid_course)
        print(f"   Unpaid user enrollment: {'✅ PASS' if not result3['success'] else '❌ FAIL'}")
        if not result3['success']:
            print(f"     Expected error: {result3.get('error_message', 'No error message')}")

        # Test enrollment success for paid user
        result4 = EnrollmentService.enroll_user_in_course(paid_user, paid_course)
        print(f"   Paid user enrollment: {'✅ PASS' if result4['success'] else '❌ FAIL'}")
        if not result4['success']:
            print(f"     Unexpected error: {result4.get('error_message', 'No error message')}")

        print("\n=== PAYMENT INTEGRATION TEST SUMMARY ===")
        test_results = [
            not result1['is_valid'],  # Regular user should be rejected
            result2['is_valid'],      # Paid user should be accepted
            not result3['success'],   # Unpaid enrollment should fail
            result4['success']        # Paid enrollment should succeed
        ]

        passed_tests = sum(test_results)
        total_tests = len(test_results)

        print(f"Tests passed: {passed_tests}/{total_tests}")
        print(f"Payment integration: {'✅ WORKING' if passed_tests == total_tests else '❌ ISSUES FOUND'}")

        return passed_tests == total_tests

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_payment_integration()
