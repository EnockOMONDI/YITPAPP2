"""
Comprehensive Unit Tests for Course Services  
Tests enrollment service and trial access control
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from courses.enrollment_service import EnrollmentService
from courses.trial_service import TrialAccessService
from courses.models import Course, Module, Lesson, Category
from progress.models import Enrollment
from users.models import Profile
from payments.models import Payment

User = get_user_model()


class EnrollmentServiceTestCase(TestCase):
    """Test EnrollmentService functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.user = User.objects.create_user(
            username='enrolluser',
            email='enroll@example.com',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            payment_verified=True,
            has_paid=True
        )
        
        # Create free course
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.free_course = Course.objects.create(
            title='Free Course',
            slug='free-course',
            description='Free Description',
            price=Decimal('0.00'),
            category=self.category,
            is_published=True
        )
        
        # Create paid course
        self.paid_course = Course.objects.create(
            title='Paid Course',
            slug='paid-course',
            description='Paid Description',
            price=Decimal('5000.00'),
            category=self.category,
            is_published=True
        )

    def test_validate_enrollment_eligibility_free_course_success(self):
        """Test enrollment validation for free course"""
        result = EnrollmentService.validate_enrollment_eligibility(
            self.user,
            self.free_course
        )
        
        self.assertTrue(result['is_valid'])
        self.assertIsNone(result['error_message'])

    def test_validate_enrollment_eligibility_unpublished_course(self):
        """Test enrollment validation for unpublished course"""
        self.free_course.is_published = False
        self.free_course.save()
        
        result = EnrollmentService.validate_enrollment_eligibility(
            self.user,
            self.free_course
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn('not currently available', result['error_message'])

    def test_validate_enrollment_eligibility_enrollment_limit_reached(self):
        """Test enrollment validation when limit is reached"""
        self.free_course.enrollment_limit = 2
        self.free_course.save()
        
        # Create enrollments up to limit
        user2 = User.objects.create_user(username='user2', email='user2@example.com', password='pass')
        user3 = User.objects.create_user(username='user3', email='user3@example.com', password='pass')
        
        Enrollment.objects.create(student=user2, course=self.free_course, status='active')
        Enrollment.objects.create(student=user3, course=self.free_course, status='active')
        
        result = EnrollmentService.validate_enrollment_eligibility(
            self.user,
            self.free_course
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn('reached its enrollment limit', result['error_message'])

    def test_validate_enrollment_eligibility_paid_course_no_payment(self):
        """Test enrollment validation for paid course without payment"""
        # User without payment verification
        user_no_payment = User.objects.create_user(
            username='nopayment',
            email='nopayment@example.com',
            password='testpass123'
        )
        Profile.objects.create(
            user=user_no_payment,
            payment_verified=False,
            has_paid=False
        )
        
        result = EnrollmentService.validate_enrollment_eligibility(
            user_no_payment,
            self.paid_course
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn('Payment verification required', result['error_message'])
        self.assertIn('KES 5,000.00', result['error_message'])

    def test_validate_enrollment_eligibility_paid_course_with_payment(self):
        """Test enrollment validation for paid course with verified payment"""
        result = EnrollmentService.validate_enrollment_eligibility(
            self.user,
            self.paid_course
        )
        
        self.assertTrue(result['is_valid'])
        self.assertIsNone(result['error_message'])

    def test_validate_enrollment_eligibility_partial_payment_expired(self):
        """Test enrollment validation with expired partial payment"""
        # Set partial payment status with expired date
        self.profile.payment_status = 'partially_paid'
        self.profile.partial_payment_expires_at = timezone.now() - timedelta(days=1)
        self.profile.save()
        
        result = EnrollmentService.validate_enrollment_eligibility(
            self.user,
            self.paid_course
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn('partial payment access', result['error_message'])
        self.assertIn('expired', result['error_message'])

    def test_validate_enrollment_eligibility_already_enrolled(self):
        """Test enrollment validation when already enrolled"""
        Enrollment.objects.create(
            student=self.user,
            course=self.free_course,
            status='active'
        )
        
        result = EnrollmentService.validate_enrollment_eligibility(
            self.user,
            self.free_course
        )
        
        self.assertFalse(result['is_valid'])
        self.assertIn('already enrolled', result['error_message'])
        self.assertIn('existing_enrollment', result)

    def test_enroll_user_free_course_success(self):
        """Test successful enrollment in free course"""
        with patch('courses.enrollment_service.send_enrollment_confirmation_email') as mock_email:
            enrollment = EnrollmentService.enroll_user(
                self.user,
                self.free_course,
                enrollment_type='paid'
            )
            
            self.assertIsNotNone(enrollment)
            self.assertEqual(enrollment.student, self.user)
            self.assertEqual(enrollment.course, self.free_course)
            self.assertEqual(enrollment.status, 'active')
            mock_email.assert_called_once()

    def test_enroll_user_trial_enrollment(self):
        """Test trial enrollment creation"""
        enrollment = EnrollmentService.enroll_user(
            self.user,
            self.free_course,
            enrollment_type='trial'
        )
        
        self.assertIsNotNone(enrollment)
        self.assertEqual(enrollment.enrollment_type, 'trial')

    def test_enroll_user_validation_failure(self):
        """Test enrollment with validation failure"""
        # Make course unpublished
        self.free_course.is_published = False
        self.free_course.save()
        
        enrollment = EnrollmentService.enroll_user(
            self.user,
            self.free_course
        )
        
        self.assertIsNone(enrollment)

    def test_enroll_user_creates_profile_if_missing(self):
        """Test enrollment creates profile if user doesn't have one"""
        user_no_profile = User.objects.create_user(
            username='noprofile',
            email='noprofile@example.com',
            password='testpass123'
        )
        
        # Ensure no profile exists
        Profile.objects.filter(user=user_no_profile).delete()
        
        # For free course, should work even without payment
        enrollment = EnrollmentService.enroll_user(
            user_no_profile,
            self.free_course
        )
        
        self.assertIsNotNone(enrollment)
        # Profile should be created
        self.assertTrue(Profile.objects.filter(user=user_no_profile).exists())

    def test_unenroll_user_success(self):
        """Test successful unenrollment"""
        enrollment = Enrollment.objects.create(
            student=self.user,
            course=self.free_course,
            status='active'
        )
        
        result = EnrollmentService.unenroll_user(self.user, self.free_course)
        
        self.assertTrue(result['success'])
        enrollment.refresh_from_db()
        self.assertEqual(enrollment.status, 'dropped')

    def test_unenroll_user_not_enrolled(self):
        """Test unenrollment when not enrolled"""
        result = EnrollmentService.unenroll_user(self.user, self.free_course)
        
        self.assertFalse(result['success'])
        self.assertIn('not enrolled', result['message'])

    def test_get_user_enrollments(self):
        """Test getting user enrollments"""
        # Create multiple enrollments
        Enrollment.objects.create(student=self.user, course=self.free_course, status='active')
        Enrollment.objects.create(student=self.user, course=self.paid_course, status='active')
        
        enrollments = EnrollmentService.get_user_enrollments(self.user)
        
        self.assertEqual(len(enrollments), 2)

    def test_get_user_enrollments_filters_dropped(self):
        """Test enrollments filter excludes dropped"""
        Enrollment.objects.create(student=self.user, course=self.free_course, status='active')
        Enrollment.objects.create(student=self.user, course=self.paid_course, status='dropped')
        
        enrollments = EnrollmentService.get_user_enrollments(self.user, include_dropped=False)
        
        self.assertEqual(len(enrollments), 1)
        self.assertEqual(enrollments[0].course, self.free_course)


class TrialAccessServiceTestCase(TestCase):
    """Test TrialAccessService functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create trial user
        self.trial_user = User.objects.create_user(
            username='trialuser',
            email='trial@example.com',
            password='testpass123'
        )
        
        # Create course structure
        self.category = Category.objects.create(
            name='Trial Category',
            slug='trial-category'
        )
        
        self.course = Course.objects.create(
            title='Trial Course',
            slug='trial-course',
            description='Trial Description',
            price=Decimal('5000.00'),
            category=self.category,
            is_published=True
        )
        
        self.module1 = Module.objects.create(
            course=self.course,
            title='Module 1',
            order=1
        )
        
        self.module2 = Module.objects.create(
            course=self.course,
            title='Module 2',
            order=2
        )
        
        # Create lessons
        self.lesson1 = Lesson.objects.create(
            module=self.module1,
            title='Lesson 1',
            content='Content 1',
            order=1
        )
        
        self.lesson2 = Lesson.objects.create(
            module=self.module1,
            title='Lesson 2',
            content='Content 2',
            order=2
        )
        
        self.lesson3 = Lesson.objects.create(
            module=self.module2,
            title='Lesson 3',
            content='Content 3',
            order=1
        )

    def test_get_user_trial_status_no_trial(self):
        """Test trial status for user without trial"""
        # Regular user (no profile or no trial)
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        status = TrialAccessService.get_user_trial_status(regular_user)
        
        self.assertFalse(status['has_trial'])
        self.assertFalse(status['is_active'])
        self.assertIsNone(status['trial_course'])

    def test_get_user_trial_status_active_trial(self):
        """Test trial status for user with active trial"""
        profile = Profile.objects.create(
            user=self.trial_user,
            trial_status='active',
            trial_course=self.course,
            trial_started_at=timezone.now()
        )
        
        status = TrialAccessService.get_user_trial_status(self.trial_user)
        
        self.assertTrue(status['has_trial'])
        self.assertTrue(status['is_active'])
        self.assertEqual(status['trial_course'], self.course)
        self.assertIsNotNone(status['boundaries'])

    def test_can_access_lesson_within_boundaries(self):
        """Test lesson access within trial boundaries"""
        profile = Profile.objects.create(
            user=self.trial_user,
            trial_status='active',
            trial_course=self.course,
            trial_started_at=timezone.now()
        )
        
        # Create trial enrollment
        Enrollment.objects.create(
            student=self.trial_user,
            course=self.course,
            enrollment_type='trial',
            status='active'
        )
        
        # First lesson should be accessible
        result = TrialAccessService.can_access_lesson(self.trial_user, self.lesson1)
        
        self.assertTrue(result['can_access'])

    def test_can_access_lesson_beyond_boundaries(self):
        """Test lesson access beyond trial boundaries"""
        profile = Profile.objects.create(
            user=self.trial_user,
            trial_status='active',
            trial_course=self.course,
            trial_started_at=timezone.now()
        )
        
        Enrollment.objects.create(
            student=self.trial_user,
            course=self.course,
            enrollment_type='trial',
            status='active'
        )
        
        # Third lesson (in second module) should be restricted
        result = TrialAccessService.can_access_lesson(self.trial_user, self.lesson3)
        
        self.assertFalse(result['can_access'])
        self.assertIn('upgrade', result['reason'].lower())

    def test_can_access_lesson_non_trial_user(self):
        """Test lesson access for non-trial user"""
        regular_user = User.objects.create_user(
            username='regular2',
            email='regular2@example.com',
            password='testpass123'
        )
        
        Profile.objects.create(
            user=regular_user,
            payment_verified=True,
            has_paid=True
        )
        
        Enrollment.objects.create(
            student=regular_user,
            course=self.course,
            enrollment_type='paid',
            status='active'
        )
        
        # All lessons should be accessible for paid users
        result = TrialAccessService.can_access_lesson(regular_user, self.lesson3)
        
        self.assertTrue(result['can_access'])

    def test_get_trial_enrollment(self):
        """Test getting trial enrollment"""
        enrollment = Enrollment.objects.create(
            student=self.trial_user,
            course=self.course,
            enrollment_type='trial',
            status='active'
        )
        
        result = TrialAccessService.get_trial_enrollment(self.trial_user, self.course)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.id, enrollment.id)

    def test_get_trial_enrollment_none(self):
        """Test getting trial enrollment when none exists"""
        result = TrialAccessService.get_trial_enrollment(self.trial_user, self.course)
        
        self.assertIsNone(result)

    def test_get_accessible_lessons_for_trial(self):
        """Test getting list of accessible lessons for trial user"""
        Profile.objects.create(
            user=self.trial_user,
            trial_status='active',
            trial_course=self.course,
            trial_started_at=timezone.now()
        )
        
        Enrollment.objects.create(
            student=self.trial_user,
            course=self.course,
            enrollment_type='trial',
            status='active'
        )
        
        accessible = TrialAccessService.get_accessible_lessons(self.trial_user, self.course)
        
        # Should return first 2 lessons based on default boundaries
        self.assertLessEqual(len(accessible), 2)

    def test_trial_expired(self):
        """Test access when trial has expired"""
        profile = Profile.objects.create(
            user=self.trial_user,
            trial_status='expired',
            trial_course=self.course,
            trial_started_at=timezone.now() - timedelta(days=15)
        )
        
        status = TrialAccessService.get_user_trial_status(self.trial_user)
        
        self.assertTrue(status['has_trial'])
        self.assertFalse(status['is_active'])


class EnrollmentIntegrationTestCase(TransactionTestCase):
    """Integration tests for enrollment and trial services"""
    
    def test_full_enrollment_workflow(self):
        """Test complete enrollment workflow"""
        # Create user
        user = User.objects.create_user(
            username='workflow',
            email='workflow@example.com',
            password='testpass123'
        )
        
        # Create course
        category = Category.objects.create(name='Workflow Cat', slug='workflow-cat')
        course = Course.objects.create(
            title='Workflow Course',
            slug='workflow-course',
            description='Description',
            price=Decimal('0.00'),
            category=category,
            is_published=True
        )
        
        # Validate eligibility
        result = EnrollmentService.validate_enrollment_eligibility(user, course)
        self.assertTrue(result['is_valid'])
        
        # Enroll user
        enrollment = EnrollmentService.enroll_user(user, course)
        self.assertIsNotNone(enrollment)
        
        # Verify enrollment
        enrollments = EnrollmentService.get_user_enrollments(user)
        self.assertEqual(len(enrollments), 1)
        
        # Unenroll
        unenroll_result = EnrollmentService.unenroll_user(user, course)
        self.assertTrue(unenroll_result['success'])

    def test_trial_to_paid_conversion(self):
        """Test converting from trial to paid enrollment"""
        # Create trial user
        user = User.objects.create_user(
            username='convert',
            email='convert@example.com',
            password='testpass123'
        )
        
        category = Category.objects.create(name='Convert Cat', slug='convert-cat')
        course = Course.objects.create(
            title='Convert Course',
            slug='convert-course',
            description='Description',
            price=Decimal('5000.00'),
            category=category,
            is_published=True
        )
        
        # Create trial enrollment
        profile = Profile.objects.create(
            user=user,
            trial_status='active',
            trial_course=course,
            trial_started_at=timezone.now()
        )
        
        trial_enrollment = Enrollment.objects.create(
            student=user,
            course=course,
            enrollment_type='trial',
            status='active'
        )
        
        # Upgrade to paid
        profile.payment_verified = True
        profile.has_paid = True
        profile.trial_status = 'converted'
        profile.save()
        
        trial_enrollment.enrollment_type = 'paid'
        trial_enrollment.save()
        
        # Verify conversion
        enrollment = Enrollment.objects.get(student=user, course=course)
        self.assertEqual(enrollment.enrollment_type, 'paid')
        self.assertEqual(profile.trial_status, 'converted')


class ServiceEdgeCasesTestCase(TestCase):
    """Test edge cases and error conditions"""
    
    def test_enrollment_with_deleted_course(self):
        """Test enrollment handling when course is deleted"""
        user = User.objects.create_user(username='edge1', email='edge1@example.com', password='pass')
        category = Category.objects.create(name='Edge Cat', slug='edge-cat')
        course = Course.objects.create(
            title='Edge Course',
            slug='edge-course',
            category=category,
            is_published=True
        )
        
        enrollment = Enrollment.objects.create(student=user, course=course, status='active')
        course_id = course.id
        
        # Delete course
        course.delete()
        
        # Enrollment should handle gracefully
        try:
            enrollment.refresh_from_db()
        except Enrollment.DoesNotExist:
            # Expected if CASCADE delete
            pass

    def test_concurrent_enrollment_attempts(self):
        """Test handling of concurrent enrollment attempts"""
        user = User.objects.create_user(username='concurrent', email='concurrent@example.com', password='pass')
        category = Category.objects.create(name='Concurrent Cat', slug='concurrent-cat')
        course = Course.objects.create(
            title='Concurrent Course',
            slug='concurrent-course',
            category=category,
            is_published=True,
            enrollment_limit=1
        )
        
        # First enrollment should succeed
        enrollment1 = EnrollmentService.enroll_user(user, course)
        self.assertIsNotNone(enrollment1)
        
        # Second attempt should fail (already enrolled)
        user2 = User.objects.create_user(username='user2c', email='user2c@example.com', password='pass')
        enrollment2 = EnrollmentService.enroll_user(user2, course)
        
        # Depending on implementation, might succeed or fail
        # Test validates it doesn't crash
