from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from .models import Enrollment, LessonProgress, QuizAttempt, Achievement
from courses.models import Course, Lesson
from assessments.models import Quiz

User = get_user_model()


class GamificationService:
    """
    Service for handling gamification features including points, badges, and achievements
    """
    
    # Points configuration
    POINTS_CONFIG = {
        'lesson_completion': 10,
        'quiz_pass_first_try': 20,
        'quiz_pass_perfect': 50,
        'quiz_pass_retake': 10,
        'module_completion': 100,
        'course_completion': 500,
        'daily_streak_bonus': 5,
        'weekly_streak_bonus': 25,
        'monthly_streak_bonus': 100,
    }
    
    # Badge thresholds
    BADGE_THRESHOLDS = {
        'lesson_completion': {
            1: {'name': 'First Steps', 'icon': 'fas fa-baby', 'description': 'Completed your first lesson'},
            5: {'name': 'Getting Started', 'icon': 'fas fa-seedling', 'description': 'Completed 5 lessons'},
            10: {'name': 'Dedicated Learner', 'icon': 'fas fa-book-reader', 'description': 'Completed 10 lessons'},
            25: {'name': 'Knowledge Seeker', 'icon': 'fas fa-search', 'description': 'Completed 25 lessons'},
            50: {'name': 'Learning Master', 'icon': 'fas fa-graduation-cap', 'description': 'Completed 50 lessons'},
            100: {'name': 'Education Champion', 'icon': 'fas fa-trophy', 'description': 'Completed 100 lessons'},
        },
        'quiz_performance': {
            1: {'name': 'Quiz Taker', 'icon': 'fas fa-question-circle', 'description': 'Passed your first quiz'},
            5: {'name': 'Quiz Master', 'icon': 'fas fa-brain', 'description': 'Passed 5 quizzes'},
            10: {'name': 'Assessment Expert', 'icon': 'fas fa-medal', 'description': 'Passed 10 quizzes'},
        },
        'perfect_scores': {
            1: {'name': 'Perfectionist', 'icon': 'fas fa-star', 'description': 'Achieved your first perfect score'},
            5: {'name': 'Excellence Seeker', 'icon': 'fas fa-gem', 'description': 'Achieved 5 perfect scores'},
            10: {'name': 'Master of Excellence', 'icon': 'fas fa-crown', 'description': 'Achieved 10 perfect scores'},
        },
        'learning_streaks': {
            3: {'name': 'Consistent Learner', 'icon': 'fas fa-fire', 'description': '3-day learning streak'},
            7: {'name': 'Weekly Warrior', 'icon': 'fas fa-calendar-week', 'description': '7-day learning streak'},
            14: {'name': 'Fortnight Fighter', 'icon': 'fas fa-calendar-alt', 'description': '14-day learning streak'},
            30: {'name': 'Monthly Master', 'icon': 'fas fa-calendar', 'description': '30-day learning streak'},
            100: {'name': 'Streak Legend', 'icon': 'fas fa-infinity', 'description': '100-day learning streak'},
        }
    }
    
    @staticmethod
    def award_lesson_completion_points(user, lesson):
        """
        Award points for lesson completion and check for achievements
        
        Args:
            user: User instance
            lesson: Lesson instance
            
        Returns:
            dict: Points awarded and achievements earned
        """
        profile = user.profile
        points_awarded = 0
        new_achievements = []
        
        # Base points for lesson completion
        base_points = GamificationService.POINTS_CONFIG['lesson_completion']
        points_awarded += base_points
        
        # Check for quiz performance bonus
        quiz = lesson.quizzes.filter(is_published=True).first()
        if quiz:
            latest_attempt = QuizAttempt.objects.filter(
                student=user,
                quiz=quiz,
                is_passed=True
            ).order_by('-completed_at').first()
            
            if latest_attempt:
                if latest_attempt.score == 100:
                    # Perfect score bonus
                    points_awarded += GamificationService.POINTS_CONFIG['quiz_pass_perfect']
                elif latest_attempt.attempt_number == 1:
                    # First try bonus
                    points_awarded += GamificationService.POINTS_CONFIG['quiz_pass_first_try']
                else:
                    # Retake bonus
                    points_awarded += GamificationService.POINTS_CONFIG['quiz_pass_retake']
        
        # Update user points
        profile.total_points = (profile.total_points or 0) + points_awarded
        
        # Update learning streak
        profile.update_learning_streak()
        
        # Check for streak bonuses
        if profile.current_streak % 7 == 0 and profile.current_streak > 0:
            streak_bonus = GamificationService.POINTS_CONFIG['weekly_streak_bonus']
            profile.total_points += streak_bonus
            points_awarded += streak_bonus
        
        profile.save()
        
        # Check and award achievements
        new_achievements.extend(GamificationService.check_and_award_lesson_achievements(user))
        new_achievements.extend(GamificationService.check_and_award_quiz_achievements(user))
        new_achievements.extend(GamificationService.check_and_award_streak_achievements(user))
        
        return {
            'points_awarded': points_awarded,
            'total_points': profile.total_points,
            'new_achievements': new_achievements,
            'current_streak': profile.current_streak
        }
    
    @staticmethod
    def check_and_award_lesson_achievements(user):
        """Check and award lesson completion achievements"""
        new_achievements = []
        
        # Count completed lessons
        completed_lessons = LessonProgress.objects.filter(
            enrollment__student=user,
            status='completed'
        ).count()
        
        # Check lesson completion badges
        for threshold, badge_data in GamificationService.BADGE_THRESHOLDS['lesson_completion'].items():
            if completed_lessons == threshold:
                achievement, created = Achievement.objects.get_or_create(
                    student=user,
                    achievement_type='lesson_completion',
                    title=badge_data['name'],
                    defaults={
                        'description': badge_data['description'],
                        'badge_icon': badge_data['icon'],
                        'points': threshold * 10
                    }
                )
                if created:
                    new_achievements.append(achievement)
        
        return new_achievements
    
    @staticmethod
    def check_and_award_quiz_achievements(user):
        """Check and award quiz performance achievements"""
        new_achievements = []
        
        # Count passed quizzes
        passed_quizzes = QuizAttempt.objects.filter(
            student=user,
            is_passed=True
        ).values('quiz').distinct().count()
        
        # Count perfect scores
        perfect_scores = QuizAttempt.objects.filter(
            student=user,
            score=100,
            is_passed=True
        ).count()
        
        # Check quiz performance badges
        for threshold, badge_data in GamificationService.BADGE_THRESHOLDS['quiz_performance'].items():
            if passed_quizzes == threshold:
                achievement, created = Achievement.objects.get_or_create(
                    student=user,
                    achievement_type='quiz_performance',
                    title=badge_data['name'],
                    defaults={
                        'description': badge_data['description'],
                        'badge_icon': badge_data['icon'],
                        'points': threshold * 15
                    }
                )
                if created:
                    new_achievements.append(achievement)
        
        # Check perfect score badges
        for threshold, badge_data in GamificationService.BADGE_THRESHOLDS['perfect_scores'].items():
            if perfect_scores == threshold:
                achievement, created = Achievement.objects.get_or_create(
                    student=user,
                    achievement_type='perfect_score',
                    title=badge_data['name'],
                    defaults={
                        'description': badge_data['description'],
                        'badge_icon': badge_data['icon'],
                        'points': threshold * 25
                    }
                )
                if created:
                    new_achievements.append(achievement)
        
        return new_achievements
    
    @staticmethod
    def check_and_award_streak_achievements(user):
        """Check and award learning streak achievements"""
        new_achievements = []
        
        profile = user.profile
        current_streak = profile.current_streak
        
        # Check streak badges
        for threshold, badge_data in GamificationService.BADGE_THRESHOLDS['learning_streaks'].items():
            if current_streak == threshold:
                achievement, created = Achievement.objects.get_or_create(
                    student=user,
                    achievement_type='streak',
                    title=badge_data['name'],
                    defaults={
                        'description': badge_data['description'],
                        'badge_icon': badge_data['icon'],
                        'points': threshold * 5
                    }
                )
                if created:
                    new_achievements.append(achievement)
        
        return new_achievements
    
    @staticmethod
    def get_user_stats(user):
        """Get comprehensive user statistics for gamification"""
        profile = user.profile
        
        # Basic stats
        total_lessons = LessonProgress.objects.filter(
            enrollment__student=user,
            status='completed'
        ).count()
        
        total_quizzes_passed = QuizAttempt.objects.filter(
            student=user,
            is_passed=True
        ).values('quiz').distinct().count()
        
        perfect_scores = QuizAttempt.objects.filter(
            student=user,
            score=100,
            is_passed=True
        ).count()
        
        total_achievements = Achievement.objects.filter(student=user).count()
        
        # Course progress
        enrollments = Enrollment.objects.filter(student=user, status='active')
        courses_completed = enrollments.filter(completion_date__isnull=False).count()
        courses_in_progress = enrollments.filter(completion_date__isnull=True).count()
        
        return {
            'total_points': profile.total_points or 0,
            'current_streak': profile.current_streak,
            'longest_streak': profile.longest_streak,
            'total_lessons_completed': total_lessons,
            'total_quizzes_passed': total_quizzes_passed,
            'perfect_scores': perfect_scores,
            'total_achievements': total_achievements,
            'courses_completed': courses_completed,
            'courses_in_progress': courses_in_progress,
            'last_activity': profile.last_activity_date
        }
    
    @staticmethod
    def get_leaderboard(limit=10):
        """Get top users by points for leaderboard"""
        from users.models import Profile
        
        top_users = Profile.objects.select_related('user').filter(
            total_points__gt=0
        ).order_by('-total_points')[:limit]
        
        leaderboard = []
        for rank, profile in enumerate(top_users, 1):
            user_stats = GamificationService.get_user_stats(profile.user)
            leaderboard.append({
                'rank': rank,
                'user': profile.user,
                'profile': profile,
                'stats': user_stats
            })
        
        return leaderboard
