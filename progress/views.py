from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from .models import Enrollment, LessonProgress, Achievement, LearningPath, StudySession
from courses.models import Course, Lesson
from users.email_utils import send_enrollment_confirmation_email, send_enrollment_admin_notification


class ProgressDashboardView(LoginRequiredMixin, TemplateView):
    """Main progress dashboard"""
    template_name = 'lms/progress/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get user's enrollments and progress
        enrollments = Enrollment.objects.filter(student=user).select_related('course')
        context['enrollments'] = enrollments
        context['total_courses'] = enrollments.count()
        context['active_courses'] = enrollments.filter(status='active').count()
        context['completed_courses'] = enrollments.filter(status='completed').count()

        # Calculate overall progress
        if enrollments.exists():
            avg_progress = enrollments.aggregate(avg_progress=Avg('progress_percentage'))['avg_progress'] or 0
            context['overall_progress'] = round(avg_progress, 1)
        else:
            context['overall_progress'] = 0

        # Recent achievements
        context['recent_achievements'] = Achievement.objects.filter(
            student=user
        ).order_by('-earned_at')[:5]

        # Study time statistics
        context['total_study_time'] = StudySession.objects.filter(
            student=user
        ).aggregate(total=Count('duration_minutes'))['total'] or 0

        return context


class MyProgressView(LoginRequiredMixin, TemplateView):
    """Detailed progress view"""
    template_name = 'lms/progress/my_progress.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get all enrollments with detailed progress
        enrollments = Enrollment.objects.filter(student=user).select_related('course')
        context['enrollments'] = enrollments

        # Get lesson progress for each enrollment
        progress_data = {}
        for enrollment in enrollments:
            lesson_progress = LessonProgress.objects.filter(enrollment=enrollment)
            progress_data[enrollment.id] = {
                'total_lessons': enrollment.course.total_lessons,
                'completed_lessons': lesson_progress.filter(status='completed').count(),
                'in_progress_lessons': lesson_progress.filter(status='in_progress').count(),
                'progress_percentage': enrollment.progress_percentage
            }

        context['progress_data'] = progress_data

        # Calculate overall progress across all enrollments
        if enrollments.exists():
            total_lessons_all = sum(enrollment.course.total_lessons for enrollment in enrollments)
            completed_lessons_all = sum(
                LessonProgress.objects.filter(
                    enrollment=enrollment,
                    status='completed'
                ).count() for enrollment in enrollments
            )
            overall_progress_percentage = (completed_lessons_all / total_lessons_all * 100) if total_lessons_all > 0 else 0

            context['overall_progress'] = {
                'total_courses': enrollments.count(),
                'total_lessons': total_lessons_all,
                'completed_lessons': completed_lessons_all,
                'progress_percentage': round(overall_progress_percentage, 1)
            }
        else:
            context['overall_progress'] = {
                'total_courses': 0,
                'total_lessons': 0,
                'completed_lessons': 0,
                'progress_percentage': 0
            }

        return context


class CourseProgressView(LoginRequiredMixin, DetailView):
    """Progress for a specific course"""
    model = Enrollment
    template_name = 'lms/progress/course_progress.html'
    context_object_name = 'enrollment'
    pk_url_kwarg = 'course_id'

    def get_object(self):
        course_id = self.kwargs['course_id']
        return get_object_or_404(
            Enrollment,
            student=self.request.user,
            course_id=course_id
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        enrollment = self.object

        # Get lesson progress
        lesson_progress = LessonProgress.objects.filter(
            enrollment=enrollment
        ).select_related('lesson', 'lesson__module').order_by(
            'lesson__module__sort_order', 'lesson__sort_order'
        )

        context['lesson_progress'] = lesson_progress

        # Group by modules
        modules_progress = {}
        for progress in lesson_progress:
            module = progress.lesson.module
            if module.id not in modules_progress:
                modules_progress[module.id] = {
                    'module': module,
                    'lessons': []
                }
            modules_progress[module.id]['lessons'].append(progress)

        context['modules_progress'] = modules_progress

        return context


class LessonProgressView(LoginRequiredMixin, DetailView):
    """Progress for a specific lesson"""
    model = LessonProgress
    template_name = 'lms/progress/lesson_progress.html'
    context_object_name = 'progress'
    pk_url_kwarg = 'lesson_id'

    def get_object(self):
        lesson_id = self.kwargs['lesson_id']
        return get_object_or_404(
            LessonProgress,
            enrollment__student=self.request.user,
            lesson_id=lesson_id
        )


class EnrollmentListView(LoginRequiredMixin, ListView):
    """List all user enrollments"""
    template_name = 'lms/progress/enrollments.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user
        ).select_related('course').order_by('-enrollment_date')


class EnrollView(LoginRequiredMixin, View):
    """Handle course enrollment using unified EnrollmentService"""

    def post(self, request, course_id):
        from courses.enrollment_service import EnrollmentService

        # Get course using the service (handles ID-based lookup)
        try:
            course = EnrollmentService.get_course_by_slug_or_id(course_id)
        except:
            messages.error(request, 'Course not found or not available for enrollment.')
            return redirect('courses:course_list')

        # Process enrollment using the unified service
        result = EnrollmentService.enroll_user_in_course(request.user, course)

        # Handle the result and provide appropriate user feedback
        if result['success']:
            # Successful enrollment
            if course.price > 0:
                messages.success(
                    request,
                    f'Successfully enrolled in "{course.title}"! Your payment has been verified. '
                    f'Check your email for confirmation details.'
                )
            else:
                messages.success(
                    request,
                    f'Successfully enrolled in "{course.title}"! Check your email for confirmation details.'
                )

            # Check for email notification issues
            if result['email_results'] and result['email_results']['errors']:
                messages.warning(
                    request,
                    'Enrollment successful, but there were issues sending confirmation emails. '
                    'Please contact support if you need assistance.'
                )
        else:
            # Failed enrollment - show specific error message
            if 'already enrolled' in result['message'].lower():
                messages.info(request, result['message'])
            else:
                messages.error(request, result['message'])

        return redirect('courses:course_detail', pk=course.id)


class UnenrollView(LoginRequiredMixin, View):
    """Handle course unenrollment"""

    def post(self, request, course_id):
        try:
            enrollment = Enrollment.objects.get(
                student=request.user,
                course_id=course_id
            )
            enrollment.status = 'dropped'
            enrollment.save()
            messages.success(request, 'Successfully unenrolled from the course.')
        except Enrollment.DoesNotExist:
            messages.error(request, 'You are not enrolled in this course.')

        return redirect('progress:enrollment_list')


class AchievementsView(LoginRequiredMixin, ListView):
    """User achievements"""
    template_name = 'lms/progress/achievements.html'
    context_object_name = 'achievements'

    def get_queryset(self):
        return Achievement.objects.filter(
            student=self.request.user
        ).order_by('-earned_at')


class LearningPathsView(LoginRequiredMixin, ListView):
    """User learning paths"""
    template_name = 'lms/progress/learning_paths.html'
    context_object_name = 'learning_paths'

    def get_queryset(self):
        return LearningPath.objects.filter(
            students=self.request.user
        ).order_by('-created_at')


class StudySessionsView(LoginRequiredMixin, ListView):
    """User study sessions"""
    template_name = 'lms/progress/study_sessions.html'
    context_object_name = 'study_sessions'

    def get_queryset(self):
        return StudySession.objects.filter(
            student=self.request.user
        ).order_by('-start_time')


class ProgressAnalyticsView(LoginRequiredMixin, TemplateView):
    """Progress analytics and statistics"""
    template_name = 'lms/progress/analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get comprehensive analytics
        enrollments = Enrollment.objects.filter(student=user)
        context['total_enrollments'] = enrollments.count()
        context['active_enrollments'] = enrollments.filter(status='active').count()
        context['completed_enrollments'] = enrollments.filter(status='completed').count()

        # Study time analytics
        study_sessions = StudySession.objects.filter(student=user)
        context['total_study_sessions'] = study_sessions.count()
        context['total_study_time'] = sum(session.duration_minutes or 0 for session in study_sessions)

        # Achievement analytics
        achievements = Achievement.objects.filter(student=user)
        context['total_achievements'] = achievements.count()

        return context


class UpdateLessonProgressView(LoginRequiredMixin, View):
    """API endpoint to update lesson progress"""

    def post(self, request):
        lesson_id = request.POST.get('lesson_id')
        status = request.POST.get('status', 'completed')

        try:
            lesson = Lesson.objects.get(id=lesson_id)
            enrollment = Enrollment.objects.get(
                student=request.user,
                course=lesson.module.course
            )

            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson
            )

            if status == 'completed':
                progress.mark_completed()
            elif status == 'started':
                progress.mark_started()

            return JsonResponse({
                'success': True,
                'status': progress.status,
                'progress_percentage': enrollment.progress_percentage
            })

        except (Lesson.DoesNotExist, Enrollment.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Invalid lesson or enrollment'})


class LeaderboardView(LoginRequiredMixin, TemplateView):
    """Gamification leaderboard view"""
    template_name = 'lms/progress/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from .services import GamificationService

        # Get leaderboard data
        context['leaderboard'] = GamificationService.get_leaderboard(limit=20)

        # Get current user's stats and rank
        user_stats = GamificationService.get_user_stats(self.request.user)
        context['user_stats'] = user_stats

        # Find user's rank
        from users.models import Profile
        user_rank = Profile.objects.filter(
            total_points__gt=self.request.user.profile.total_points or 0
        ).count() + 1
        context['user_rank'] = user_rank

        return context


class AchievementsView(LoginRequiredMixin, ListView):
    """User achievements view"""
    template_name = 'lms/progress/achievements.html'
    context_object_name = 'achievements'

    def get_queryset(self):
        return Achievement.objects.filter(
            student=self.request.user
        ).order_by('-earned_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from .services import GamificationService

        # Get user stats
        context['user_stats'] = GamificationService.get_user_stats(self.request.user)

        # Group achievements by type
        achievements_by_type = {}
        for achievement in context['achievements']:
            if achievement.achievement_type not in achievements_by_type:
                achievements_by_type[achievement.achievement_type] = []
            achievements_by_type[achievement.achievement_type].append(achievement)

        context['achievements_by_type'] = achievements_by_type

        return context


class StartStudySessionView(LoginRequiredMixin, View):
    """API endpoint to start a study session"""

    def post(self, request):
        course_id = request.POST.get('course_id')

        try:
            course = Course.objects.get(id=course_id)
            session = StudySession.objects.create(
                student=request.user,
                course=course,
                start_time=timezone.now()
            )

            return JsonResponse({
                'success': True,
                'session_id': session.id
            })

        except Course.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid course'})


class EndStudySessionView(LoginRequiredMixin, View):
    """API endpoint to end a study session"""

    def post(self, request):
        session_id = request.POST.get('session_id')

        try:
            session = StudySession.objects.get(
                id=session_id,
                student=request.user,
                end_time__isnull=True
            )

            session.end_time = timezone.now()
            session.save()

            return JsonResponse({
                'success': True,
                'duration': session.duration_minutes
            })

        except StudySession.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid session'})


class UpdateStudyGoalsView(LoginRequiredMixin, View):
    """API endpoint to update study goals"""

    def post(self, request):
        daily_goal = request.POST.get('daily_goal')
        weekly_goal = request.POST.get('weekly_goal')

        try:
            # Here you would typically update user's study goals
            # For now, just return success
            return JsonResponse({
                'success': True,
                'message': 'Study goals updated successfully'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
