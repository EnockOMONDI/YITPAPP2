"""
Trial Access Control Service for YITP
Handles trial user access control for lessons, quizzes, and course content
"""

from django.utils import timezone
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


class TrialAccessService:
    """
    Service for managing trial user access to course content
    """
    
    # Default trial boundaries
    DEFAULT_TRIAL_BOUNDARIES = {
        'max_lessons': 2,
        'max_modules': 1,
        'trial_duration_days': 10
    }
    
    @staticmethod
    def get_user_trial_status(user):
        """
        Get comprehensive trial status for a user
        
        Returns:
            dict: {
                'has_trial': bool,
                'is_active': bool,
                'trial_course': Course or None,
                'trial_started_at': datetime or None,
                'boundaries': dict
            }
        """
        try:
            profile = user.profile
            return {
                'has_trial': profile.trial_status != 'none',
                'is_active': profile.has_active_trial,
                'trial_course': profile.trial_course,
                'trial_started_at': profile.trial_started_at,
                'boundaries': TrialAccessService.DEFAULT_TRIAL_BOUNDARIES
            }
        except:
            return {
                'has_trial': False,
                'is_active': False,
                'trial_course': None,
                'trial_started_at': None,
                'boundaries': {}
            }
    
    @staticmethod
    def get_trial_enrollment(user, course):
        """
        Get trial enrollment for user and course
        
        Returns:
            Enrollment or None
        """
        from progress.models import Enrollment
        
        try:
            return Enrollment.objects.get(
                student=user,
                course=course,
                enrollment_type='trial'
            )
        except Enrollment.DoesNotExist:
            return None
    
    @staticmethod
    def can_access_lesson(user, lesson):
        """
        Check if user can access a specific lesson based on trial boundaries
        
        Args:
            user: User object
            lesson: Lesson object
            
        Returns:
            dict: {
                'can_access': bool,
                'reason': str,
                'is_trial_user': bool,
                'lesson_position': int or None
            }
        """
        # Get user's trial status
        trial_status = TrialAccessService.get_user_trial_status(user)
        
        # Non-trial users or users with paid access have full access
        if not trial_status['is_active']:
            # Check if user has paid access
            try:
                profile = user.profile
                if profile.has_any_payment_access:
                    return {
                        'can_access': True,
                        'reason': 'User has paid access',
                        'is_trial_user': False,
                        'lesson_position': None
                    }
            except:
                pass
            
            # Check if user has regular enrollment
            from progress.models import Enrollment
            enrollment = Enrollment.objects.filter(
                student=user,
                course=lesson.module.course,
                enrollment_type='paid'
            ).first()
            
            if enrollment:
                return {
                    'can_access': True,
                    'reason': 'User has paid enrollment',
                    'is_trial_user': False,
                    'lesson_position': None
                }
            
            return {
                'can_access': False,
                'reason': 'No access - enrollment required',
                'is_trial_user': False,
                'lesson_position': None
            }
        
        # Trial user - check boundaries
        trial_enrollment = TrialAccessService.get_trial_enrollment(user, lesson.module.course)
        if not trial_enrollment:
            return {
                'can_access': False,
                'reason': 'No trial enrollment found',
                'is_trial_user': True,
                'lesson_position': None
            }
        
        # Check if lesson is within trial boundaries
        can_access = trial_enrollment.can_access_lesson_in_trial(lesson)
        
        # Get lesson position for context
        course_lessons = lesson.module.course.get_ordered_lessons()
        try:
            lesson_position = list(course_lessons).index(lesson) + 1
        except ValueError:
            lesson_position = None
        
        if can_access:
            return {
                'can_access': True,
                'reason': f'Trial access granted (lesson {lesson_position})',
                'is_trial_user': True,
                'lesson_position': lesson_position
            }
        else:
            return {
                'can_access': False,
                'reason': f'Trial boundary exceeded (lesson {lesson_position} > 2)',
                'is_trial_user': True,
                'lesson_position': lesson_position
            }
    
    @staticmethod
    def can_access_quiz(user, quiz):
        """
        Check if user can access a specific quiz based on trial boundaries
        
        Args:
            user: User object
            quiz: Quiz object
            
        Returns:
            dict: {
                'can_access': bool,
                'reason': str,
                'is_trial_user': bool,
                'associated_lesson': Lesson or None
            }
        """
        # Get user's trial status
        trial_status = TrialAccessService.get_user_trial_status(user)
        
        # Non-trial users or users with paid access have full access
        if not trial_status['is_active']:
            # Check if user has paid access
            try:
                profile = user.profile
                if profile.has_any_payment_access:
                    return {
                        'can_access': True,
                        'reason': 'User has paid access',
                        'is_trial_user': False,
                        'associated_lesson': getattr(quiz, 'lesson', None)
                    }
            except:
                pass
            
            # Check if user has regular enrollment
            from progress.models import Enrollment
            enrollment = Enrollment.objects.filter(
                student=user,
                course=quiz.course,
                enrollment_type='paid'
            ).first()
            
            if enrollment:
                return {
                    'can_access': True,
                    'reason': 'User has paid enrollment',
                    'is_trial_user': False,
                    'associated_lesson': getattr(quiz, 'lesson', None)
                }
            
            return {
                'can_access': False,
                'reason': 'No access - enrollment required',
                'is_trial_user': False,
                'associated_lesson': getattr(quiz, 'lesson', None)
            }
        
        # Trial user - check boundaries
        trial_enrollment = TrialAccessService.get_trial_enrollment(user, quiz.course)
        if not trial_enrollment:
            return {
                'can_access': False,
                'reason': 'No trial enrollment found',
                'is_trial_user': True,
                'associated_lesson': getattr(quiz, 'lesson', None)
            }
        
        # Check if quiz is within trial boundaries
        can_access = trial_enrollment.can_access_quiz_in_trial(quiz)
        associated_lesson = getattr(quiz, 'lesson', None)
        
        if can_access:
            return {
                'can_access': True,
                'reason': 'Trial access granted for quiz',
                'is_trial_user': True,
                'associated_lesson': associated_lesson
            }
        else:
            return {
                'can_access': False,
                'reason': 'Quiz not accessible in trial',
                'is_trial_user': True,
                'associated_lesson': associated_lesson
            }
    
    @staticmethod
    def get_trial_progress_summary(user, course):
        """
        Get trial progress summary for a user and course
        
        Returns:
            dict: {
                'is_trial_user': bool,
                'accessible_lessons': list,
                'completed_lessons': list,
                'accessible_quizzes': list,
                'completed_quizzes': list,
                'trial_completion_percentage': float,
                'next_action': str
            }
        """
        trial_status = TrialAccessService.get_user_trial_status(user)
        
        if not trial_status['is_active']:
            return {
                'is_trial_user': False,
                'accessible_lessons': [],
                'completed_lessons': [],
                'accessible_quizzes': [],
                'completed_quizzes': [],
                'trial_completion_percentage': 0.0,
                'next_action': 'Not a trial user'
            }
        
        trial_enrollment = TrialAccessService.get_trial_enrollment(user, course)
        if not trial_enrollment:
            return {
                'is_trial_user': True,
                'accessible_lessons': [],
                'completed_lessons': [],
                'accessible_quizzes': [],
                'completed_quizzes': [],
                'trial_completion_percentage': 0.0,
                'next_action': 'No trial enrollment found'
            }
        
        # Get accessible lessons
        accessible_lessons = trial_enrollment.get_trial_accessible_lessons()
        
        # Get completed lessons
        from progress.models import LessonProgress
        completed_lessons = LessonProgress.objects.filter(
            enrollment=trial_enrollment,
            lesson__in=accessible_lessons,
            status='completed'
        ).values_list('lesson', flat=True)
        
        # Get accessible quizzes
        accessible_quizzes = []
        for lesson in accessible_lessons:
            if hasattr(lesson, 'quiz') and lesson.quiz:
                accessible_quizzes.append(lesson.quiz)
        
        # Get completed quizzes
        from assessments.models import QuizAttempt
        completed_quizzes = QuizAttempt.objects.filter(
            user=user,
            quiz__in=accessible_quizzes,
            passed=True
        ).values_list('quiz', flat=True)
        
        # Calculate trial completion percentage
        total_trial_items = len(accessible_lessons) + len(accessible_quizzes)
        completed_items = len(completed_lessons) + len(completed_quizzes)
        trial_completion_percentage = (completed_items / total_trial_items * 100) if total_trial_items > 0 else 0
        
        # Determine next action
        if trial_completion_percentage >= 100:
            next_action = 'Trial completed - upgrade to continue'
        elif len(completed_lessons) < len(accessible_lessons):
            next_action = f'Continue with lesson {len(completed_lessons) + 1}'
        else:
            next_action = 'Complete remaining quizzes'
        
        return {
            'is_trial_user': True,
            'accessible_lessons': list(accessible_lessons),
            'completed_lessons': list(completed_lessons),
            'accessible_quizzes': accessible_quizzes,
            'completed_quizzes': list(completed_quizzes),
            'trial_completion_percentage': trial_completion_percentage,
            'next_action': next_action
        }
    
    @staticmethod
    def track_trial_access(user, content_type, content_id):
        """
        Track trial user's access to content
        
        Args:
            user: User object
            content_type: 'lesson' or 'quiz'
            content_id: ID of the content
        """
        try:
            profile = user.profile
            if profile.has_active_trial:
                if content_type == 'lesson':
                    profile.track_trial_lesson_access(content_id)
                elif content_type == 'quiz':
                    profile.track_trial_quiz_access(content_id)
        except Exception as e:
            logger.error(f"Failed to track trial access for user {user.id}: {str(e)}")
    
    @staticmethod
    def should_show_upgrade_prompt(user, course):
        """
        Determine if upgrade prompt should be shown to trial user
        
        Returns:
            dict: {
                'show_prompt': bool,
                'reason': str,
                'prompt_type': str  # 'boundary_reached', 'trial_complete', 'trial_expired'
            }
        """
        trial_status = TrialAccessService.get_user_trial_status(user)
        
        if not trial_status['has_trial']:
            return {
                'show_prompt': False,
                'reason': 'Not a trial user',
                'prompt_type': None
            }
        
        if trial_status['trial_course'] != course:
            return {
                'show_prompt': False,
                'reason': 'Trial is for different course',
                'prompt_type': None
            }
        
        # Check if trial has expired
        if user.profile.trial_status == 'expired':
            return {
                'show_prompt': True,
                'reason': 'Trial has expired',
                'prompt_type': 'trial_expired'
            }
        
        # Check trial progress
        progress_summary = TrialAccessService.get_trial_progress_summary(user, course)
        
        if progress_summary['trial_completion_percentage'] >= 100:
            return {
                'show_prompt': True,
                'reason': 'Trial content completed',
                'prompt_type': 'trial_complete'
            }
        
        return {
            'show_prompt': False,
            'reason': 'Trial still in progress',
            'prompt_type': None
        }
