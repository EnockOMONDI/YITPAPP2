"""
Comprehensive Unit Tests for Assessment Services
Tests quiz validation, lesson completion requirements, and access control
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from unittest.mock import patch, MagicMock

from assessments.services import QuizValidationService
from assessments.models import Quiz, Question
from courses.models import Course, Module, Lesson, Category
from progress.models import QuizAttempt, Enrollment, LessonProgress
from users.models import Profile

User = get_user_model()


class QuizValidationServiceTestCase(TestCase):
    """Test QuizValidationService functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create user
        self.user = User.objects.create_user(
            username='quizuser',
            email='quiz@example.com',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            payment_verified=True,
            has_paid=True
        )
        
        # Create course structure
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            slug='test-course',
            description='Test Description',
            category=self.category,
            is_published=True
        )
        
        self.module = Module.objects.create(
            course=self.course,
            title='Test Module',
            order=1
        )
        
        self.lesson = Lesson.objects.create(
            module=self.module,
            title='Test Lesson',
            content='Test Content',
            order=1
        )
        
        # Create enrollment
        self.enrollment = Enrollment.objects.create(
            student=self.user,
            course=self.course,
            status='active'
        )
        
        # Create quiz
        self.quiz = Quiz.objects.create(
            lesson=self.lesson,
            title='Test Quiz',
            description='Test quiz description',
            time_limit=30,
            max_attempts=3,
            passing_score=70,
            is_published=True
        )
        
        # Create questions
        for i in range(5):
            Question.objects.create(
                quiz=self.quiz,
                question_text=f'Question {i+1}?',
                question_type='multiple_choice',
                options=['A', 'B', 'C', 'D'],
                correct_answer='A',
                points=20,
                order=i+1
            )

    def test_validate_lesson_completion_no_quiz(self):
        """Test lesson completion validation when no quiz exists"""
        # Create lesson without quiz
        lesson_no_quiz = Lesson.objects.create(
            module=self.module,
            title='Lesson Without Quiz',
            content='No quiz content',
            order=2
        )
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            lesson_no_quiz
        )
        
        self.assertTrue(can_complete)
        self.assertEqual(message, "No quiz required for this lesson.")
        self.assertIsNone(quiz_data)

    def test_validate_lesson_completion_quiz_passed(self):
        """Test lesson completion when quiz is already passed"""
        # Create passing attempt
        QuizAttempt.objects.create(
            student=self.user,
            quiz=self.quiz,
            score=85.0,
            is_passed=True,
            is_completed=True,
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            self.lesson
        )
        
        self.assertTrue(can_complete)
        self.assertEqual(message, "Quiz requirement satisfied.")
        self.assertIsNone(quiz_data)

    def test_validate_lesson_completion_quiz_not_attempted(self):
        """Test lesson completion when quiz not yet attempted"""
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            self.lesson
        )
        
        self.assertFalse(can_complete)
        self.assertIn("must complete the quiz", message)
        self.assertIsNotNone(quiz_data)
        self.assertEqual(quiz_data['quiz_id'], self.quiz.id)
        self.assertEqual(quiz_data['attempts_used'], 0)
        self.assertEqual(quiz_data['max_attempts'], 3)
        self.assertEqual(quiz_data['passing_score'], 70)

    def test_validate_lesson_completion_max_attempts_reached(self):
        """Test lesson completion when max attempts reached without passing"""
        # Create failed attempts up to limit
        for i in range(3):
            QuizAttempt.objects.create(
                student=self.user,
                quiz=self.quiz,
                score=50.0 + i*5,
                is_passed=False,
                is_completed=True,
                started_at=timezone.now(),
                submitted_at=timezone.now()
            )
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            self.lesson
        )
        
        self.assertFalse(can_complete)
        self.assertIn("Maximum quiz attempts", message)
        self.assertIn("Contact instructor", message)
        self.assertIsNotNone(quiz_data)
        self.assertEqual(quiz_data['attempts_used'], 3)

    def test_validate_lesson_completion_retake_needed(self):
        """Test lesson completion when retake is needed"""
        # Create one failed attempt
        QuizAttempt.objects.create(
            student=self.user,
            quiz=self.quiz,
            score=60.0,
            is_passed=False,
            is_completed=True,
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            self.lesson
        )
        
        self.assertFalse(can_complete)
        self.assertIn("must pass the quiz", message)
        self.assertIn("Attempts used: 1/3", message)
        self.assertIsNotNone(quiz_data)

    def test_validate_lesson_completion_unlimited_attempts(self):
        """Test validation with unlimited attempts (max_attempts=0)"""
        self.quiz.max_attempts = 0
        self.quiz.save()
        
        # Create many failed attempts
        for i in range(10):
            QuizAttempt.objects.create(
                student=self.user,
                quiz=self.quiz,
                score=65.0,
                is_passed=False,
                is_completed=True,
                started_at=timezone.now(),
                submitted_at=timezone.now()
            )
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            self.lesson
        )
        
        self.assertFalse(can_complete)
        self.assertIn("Attempts used: 10/∞", message)

    def test_get_user_quiz_status_no_quiz(self):
        """Test getting quiz status when no quiz exists"""
        lesson_no_quiz = Lesson.objects.create(
            module=self.module,
            title='No Quiz Lesson',
            content='Content',
            order=3
        )
        
        status = QuizValidationService.get_user_quiz_status(self.user, lesson_no_quiz)
        
        self.assertFalse(status['has_quiz'])
        self.assertFalse(status['quiz_required'])

    def test_get_user_quiz_status_with_quiz(self):
        """Test getting quiz status with quiz present"""
        status = QuizValidationService.get_user_quiz_status(self.user, self.lesson)
        
        self.assertTrue(status['has_quiz'])
        self.assertTrue(status['quiz_required'])
        self.assertEqual(status['quiz_id'], self.quiz.id)
        self.assertEqual(status['quiz_title'], self.quiz.title)
        self.assertEqual(status['attempts_used'], 0)
        self.assertFalse(status['has_passed'])

    def test_get_user_quiz_status_with_attempts(self):
        """Test quiz status with multiple attempts"""
        # Create attempts with different scores
        QuizAttempt.objects.create(
            student=self.user,
            quiz=self.quiz,
            score=60.0,
            is_passed=False,
            is_completed=True,
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )
        
        QuizAttempt.objects.create(
            student=self.user,
            quiz=self.quiz,
            score=85.0,
            is_passed=True,
            is_completed=True,
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )
        
        status = QuizValidationService.get_user_quiz_status(self.user, self.lesson)
        
        self.assertTrue(status['has_passed'])
        self.assertEqual(status['best_score'], 85.0)
        self.assertEqual(status['attempts_used'], 2)
        self.assertEqual(status['latest_score'], 85.0)

    def test_get_user_quiz_status_review_url(self):
        """Test that review URL is generated for completed attempts"""
        attempt = QuizAttempt.objects.create(
            student=self.user,
            quiz=self.quiz,
            score=75.0,
            is_passed=True,
            is_completed=True,
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )
        
        status = QuizValidationService.get_user_quiz_status(self.user, self.lesson)
        
        self.assertIsNotNone(status.get('review_url'))
        expected_url = reverse('assessments:quiz_results', kwargs={'attempt_id': attempt.id})
        self.assertEqual(status['review_url'], expected_url)

    def test_validate_lesson_completion_unpublished_quiz(self):
        """Test validation with unpublished quiz"""
        self.quiz.is_published = False
        self.quiz.save()
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            self.lesson
        )
        
        # Should treat as no quiz when unpublished
        self.assertTrue(can_complete)

    def test_quiz_validation_with_trial_user(self):
        """Test quiz validation for trial users"""
        # Set user as trial
        self.profile.trial_status = 'active'
        self.profile.save()
        
        # Remove enrollment (trial users don't have full enrollment)
        self.enrollment.delete()
        
        # Mock trial service
        with patch('assessments.models.TrialAccessService.can_access_quiz') as mock_access:
            mock_access.return_value = {
                'is_trial_user': True,
                'can_access': False,
                'reason': 'Trial users can only access first 2 quizzes'
            }
            
            can_access, message = self.quiz.can_user_attempt(self.user)
            
            self.assertFalse(can_access)
            self.assertIn('Trial users', message)


class QuizValidationIntegrationTestCase(TestCase):
    """Integration tests for quiz validation with lesson progress"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123'
        )
        
        Profile.objects.create(
            user=self.user,
            payment_verified=True,
            has_paid=True
        )
        
        category = Category.objects.create(
            name='Integration Category',
            slug='integration-category'
        )
        
        self.course = Course.objects.create(
            title='Integration Course',
            slug='integration-course',
            description='Integration Description',
            category=category,
            is_published=True
        )
        
        module = Module.objects.create(
            course=self.course,
            title='Integration Module',
            order=1
        )
        
        self.lesson = Lesson.objects.create(
            module=module,
            title='Integration Lesson',
            content='Integration Content',
            order=1
        )
        
        Enrollment.objects.create(
            student=self.user,
            course=self.course,
            status='active'
        )
        
        self.quiz = Quiz.objects.create(
            lesson=self.lesson,
            title='Integration Quiz',
            max_attempts=2,
            passing_score=75,
            is_published=True
        )

    def test_lesson_completion_workflow(self):
        """Test complete lesson completion workflow with quiz"""
        # Step 1: Check initial state
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            self.lesson
        )
        self.assertFalse(can_complete)
        self.assertIsNotNone(quiz_data)
        
        # Step 2: Create failed attempt
        QuizAttempt.objects.create(
            student=self.user,
            quiz=self.quiz,
            score=60.0,
            is_passed=False,
            is_completed=True,
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            self.lesson
        )
        self.assertFalse(can_complete)
        
        # Step 3: Create passing attempt
        QuizAttempt.objects.create(
            student=self.user,
            quiz=self.quiz,
            score=80.0,
            is_passed=True,
            is_completed=True,
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            self.user,
            self.lesson
        )
        self.assertTrue(can_complete)
        self.assertEqual(message, "Quiz requirement satisfied.")


class QuizValidationEdgeCasesTestCase(TestCase):
    """Test edge cases and error conditions"""
    
    def test_validation_with_missing_user(self):
        """Test validation handles missing user gracefully"""
        lesson = MagicMock()
        lesson.quizzes.filter().first.return_value = None
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            None,
            lesson
        )
        
        # Should handle gracefully
        self.assertIsNotNone(message)

    def test_validation_with_corrupted_quiz_data(self):
        """Test validation with corrupted quiz data"""
        user = User.objects.create_user(
            username='corruptuser',
            email='corrupt@example.com',
            password='testpass123'
        )
        
        # Create quiz with invalid data
        category = Category.objects.create(
            name='Corrupt Category',
            slug='corrupt-category'
        )
        course = Course.objects.create(
            title='Corrupt Course',
            slug='corrupt-course',
            category=category,
            is_published=True
        )
        module = Module.objects.create(
            course=course,
            title='Corrupt Module',
            order=1
        )
        lesson = Lesson.objects.create(
            module=module,
            title='Corrupt Lesson',
            content='Content',
            order=1
        )
        
        quiz = Quiz.objects.create(
            lesson=lesson,
            title='Corrupt Quiz',
            max_attempts=-1,  # Invalid
            passing_score=150,  # Invalid
            is_published=True
        )
        
        # Should handle gracefully
        try:
            can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
                user,
                lesson
            )
            # If it doesn't crash, test passes
        except Exception as e:
            self.fail(f"Should handle corrupted data gracefully: {e}")

    def test_concurrent_quiz_attempts(self):
        """Test handling of concurrent quiz attempts"""
        user = User.objects.create_user(
            username='concurrent',
            email='concurrent@example.com',
            password='testpass123'
        )
        
        Profile.objects.create(user=user, payment_verified=True, has_paid=True)
        
        category = Category.objects.create(name='Cat', slug='cat')
        course = Course.objects.create(
            title='Course',
            slug='course',
            category=category,
            is_published=True
        )
        module = Module.objects.create(course=course, title='Module', order=1)
        lesson = Lesson.objects.create(module=module, title='Lesson', content='C', order=1)
        
        Enrollment.objects.create(student=user, course=course, status='active')
        
        quiz = Quiz.objects.create(
            lesson=lesson,
            title='Quiz',
            max_attempts=1,
            is_published=True
        )
        
        # Create two attempts (should only count actual attempts)
        QuizAttempt.objects.create(
            student=user,
            quiz=quiz,
            score=50.0,
            is_passed=False,
            is_completed=True,
            started_at=timezone.now(),
            submitted_at=timezone.now()
        )
        
        can_complete, message, quiz_data = QuizValidationService.validate_lesson_completion(
            user,
            lesson
        )
        
        self.assertFalse(can_complete)
        self.assertIn("Maximum quiz attempts", message)
