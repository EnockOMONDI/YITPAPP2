from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Quiz, Question
from progress.models import QuizAttempt, Enrollment, LessonProgress

User = get_user_model()


class QuizValidationService:
    """
    Service for handling quiz validation and lesson completion requirements
    """
    
    @staticmethod
    def validate_lesson_completion(user, lesson):
        """
        Validate if user can complete lesson based on quiz requirements
        
        Args:
            user: User instance
            lesson: Lesson instance
            
        Returns:
            tuple: (can_complete: bool, message: str, quiz_data: dict or None)
        """
        # Check if lesson has any published quizzes
        quiz = lesson.quizzes.filter(is_published=True).first()
        if not quiz:
            return True, "No quiz required for this lesson.", None
        
        # Check for passing attempt
        passed_attempt = QuizAttempt.objects.filter(
            student=user,
            quiz=quiz,
            is_passed=True
        ).exists()
        
        if passed_attempt:
            return True, "Quiz requirement satisfied.", None
        
        # Check attempts remaining
        attempts_count = QuizAttempt.objects.filter(
            student=user,
            quiz=quiz
        ).count()
        
        if attempts_count >= quiz.max_attempts and quiz.max_attempts > 0:
            return False, f"Maximum quiz attempts ({quiz.max_attempts}) reached. Contact instructor for help.", {
                'quiz_id': quiz.id,
                'attempts_used': attempts_count,
                'max_attempts': quiz.max_attempts,
                'passing_score': quiz.passing_score
            }
        
        # User needs to take/retake the quiz
        quiz_data = {
            'quiz_id': quiz.id,
            'quiz_title': quiz.title,
            'quiz_url': reverse('assessments:take_quiz', kwargs={'quiz_id': quiz.id}),
            'attempts_used': attempts_count,
            'max_attempts': quiz.max_attempts,
            'passing_score': quiz.passing_score,
            'time_limit': quiz.time_limit
        }
        
        if attempts_count == 0:
            message = f"You must complete the quiz '{quiz.title}' (minimum {quiz.passing_score}%) to complete this lesson."
        else:
            message = f"You must pass the quiz '{quiz.title}' (minimum {quiz.passing_score}%) to complete this lesson. Attempts used: {attempts_count}/{quiz.max_attempts if quiz.max_attempts > 0 else '∞'}"
        
        return False, message, quiz_data
    
    @staticmethod
    def get_user_quiz_status(user, lesson):
        """
        Get detailed quiz status for a user and lesson
        
        Args:
            user: User instance
            lesson: Lesson instance
            
        Returns:
            dict: Quiz status information
        """
        quiz = lesson.quizzes.filter(is_published=True).first()
        if not quiz:
            return {
                'has_quiz': False,
                'quiz_required': False
            }
        
        attempts = QuizAttempt.objects.filter(
            student=user,
            quiz=quiz
        ).order_by('-started_at')
        
        best_attempt = attempts.filter(is_passed=True).order_by('-score').first()
        latest_attempt = attempts.first()
        last_attempt_id = latest_attempt.id if latest_attempt else None
        review_url = reverse('assessments:quiz_results', kwargs={'attempt_id': last_attempt_id}) if last_attempt_id else None
        
        can_attempt = (
            best_attempt is None and
            (quiz.max_attempts == 0 or attempts.count() < quiz.max_attempts)
        )

        return {
            'has_quiz': True,
            'quiz_required': True,
            'quiz': quiz,
            'quiz_url': reverse('assessments:take_quiz', kwargs={'quiz_id': quiz.id}),
            'attempts_count': attempts.count(),
            'max_attempts': quiz.max_attempts,
            'can_attempt': can_attempt,
            'has_passed': best_attempt is not None,
            'best_score': float(best_attempt.score) if best_attempt else None,
            'latest_score': float(latest_attempt.score) if latest_attempt and latest_attempt.score else None,
            'passing_score': quiz.passing_score,
            'time_limit': quiz.time_limit,
            'last_attempt_id': last_attempt_id,
            'review_url': review_url,
        }
    
    @staticmethod
    def check_quiz_prerequisites(user, quiz):
        """
        Check if user meets prerequisites to take a quiz
        
        Args:
            user: User instance
            quiz: Quiz instance
            
        Returns:
            tuple: (can_take: bool, message: str)
        """
        # Check if user is enrolled in the course
        try:
            enrollment = Enrollment.objects.get(
                student=user,
                course=quiz.lesson.module.course,
                status='active'
            )
        except Enrollment.DoesNotExist:
            return False, "You must be enrolled in this course to take quizzes."
        
        # Check if lesson is accessible
        is_accessible, access_message = quiz.lesson.is_accessible_for_user(user)
        if not is_accessible:
            return False, f"Lesson not accessible: {access_message}"
        
        # Check attempt limits
        attempts_count = QuizAttempt.objects.filter(
            student=user,
            quiz=quiz
        ).count()
        
        if quiz.max_attempts > 0 and attempts_count >= quiz.max_attempts:
            return False, f"Maximum attempts ({quiz.max_attempts}) reached for this quiz."
        
        return True, "Quiz is available to take."
