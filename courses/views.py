from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from .models import Course, Category, Module, Lesson
from progress.models import Enrollment, LessonProgress
from users.email_utils import send_enrollment_confirmation_email, send_enrollment_admin_notification


User = get_user_model()


class HomeView(TemplateView):
    """
    Homepage view
    """
    template_name = 'lms/courses/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_courses'] = Course.objects.filter(is_published=True, is_featured=True)[:6]
        context['categories'] = Category.objects.filter(is_active=True, parent=None)[:8]
        return context


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Student dashboard view
    """
    template_name = 'lms/courses/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user enrollments
        enrollments = Enrollment.objects.filter(student=user, status='active').select_related('course')
        context['enrollments'] = enrollments
        
        # Get recent activity
        recent_progress = LessonProgress.objects.filter(
            enrollment__student=user
        ).order_by('-completed_at')[:5]
        context['recent_progress'] = recent_progress
        
        # Get user profile
        try:
            context['user_profile'] = user.profile
        except:
            context['user_profile'] = None
        
        return context


class CourseListView(ListView):
    """
    Course listing view
    """
    model = Course
    template_name = 'lms/courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Course.objects.filter(is_published=True).select_related('instructor', 'category')
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by difficulty
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty_level=difficulty)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['current_category'] = self.request.GET.get('category', '')
        context['current_difficulty'] = self.request.GET.get('difficulty', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context


class CourseDetailView(DetailView):
    """
    Course detail view
    """
    model = Course
    template_name = 'lms/courses/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object

        # Get course modules and lessons with progress
        modules = course.modules.filter(is_published=True).prefetch_related(
            'lessons__student_progress'
        ).order_by('sort_order')

        # Add lesson accessibility information if user is enrolled
        if self.request.user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(
                    student=self.request.user,
                    course=course,
                    status='active'
                )

                # Process each module and lesson for accessibility
                for module in modules:
                    lessons = module.lessons.filter(is_published=True).order_by('sort_order')
                    lesson_data = []
                    for lesson in lessons:
                        try:
                            progress = LessonProgress.objects.get(
                                enrollment=enrollment,
                                lesson=lesson
                            )
                        except LessonProgress.DoesNotExist:
                            progress = None

                        is_accessible, _ = lesson.is_accessible_for_user(self.request.user)
                        lesson_data.append({
                            'lesson': lesson,
                            'progress': progress,
                            'is_accessible': is_accessible
                        })

                    module.lesson_data = lesson_data

            except Enrollment.DoesNotExist:
                pass

        context['modules'] = modules

        # Check if user is enrolled and get progress
        enrollment = None
        user_progress = {}
        if self.request.user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(student=self.request.user, course=course)
                context['enrollment'] = enrollment
                context['is_enrolled'] = True

                # Get user's lesson progress
                lesson_progress = LessonProgress.objects.filter(
                    enrollment=enrollment
                ).select_related('lesson')

                for progress in lesson_progress:
                    user_progress[progress.lesson.id] = progress

            except Enrollment.DoesNotExist:
                context['is_enrolled'] = False
        else:
            context['is_enrolled'] = False

        context['user_progress'] = user_progress

        # Get course reviews and calculate average rating
        reviews = course.reviews.filter(is_published=True).select_related('student')
        context['reviews'] = reviews[:5]  # Show first 5 reviews
        context['all_reviews'] = reviews  # For rating calculation

        # Calculate average rating
        if reviews.exists():
            total_rating = sum(review.rating for review in reviews)
            context['average_rating'] = round(total_rating / reviews.count(), 1)
            context['rating_count'] = reviews.count()
        else:
            context['average_rating'] = 0
            context['rating_count'] = 0

        # Get instructor profile
        try:
            context['instructor_profile'] = course.instructor.profile
        except:
            context['instructor_profile'] = None

        # Calculate course statistics
        context['total_lessons'] = course.total_lessons
        context['total_modules'] = course.total_modules
        context['enrolled_count'] = course.enrolled_students_count

        # Get related courses (same category)
        context['related_courses'] = Course.objects.filter(
            category=course.category,
            is_published=True
        ).exclude(id=course.id)[:3]

        return context


class EnrollView(LoginRequiredMixin, TemplateView):
    """
    Course enrollment view
    """
    def post(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug, is_published=True)

        # Check payment verification for paid courses
        if course.price > 0:
            # Get or create user profile
            profile, created = request.user.profile, False
            try:
                profile = request.user.profile
            except:
                from users.models import Profile
                profile = Profile.objects.create(user=request.user)

            # Check if payment is confirmed for paid courses
            if not profile.has_confirmed_payment:
                messages.error(
                    request,
                    f'Payment verification required for {course.title}. '
                    f'This course costs KES {course.price}. Please complete your payment '
                    f'and wait for confirmation before enrolling. Contact support for payment instructions.'
                )
                return redirect('courses:course_detail', slug=course_slug)

        # Check if already enrolled
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'status': 'active'}
        )

        if created:
            # Send enrollment confirmation email to user
            try:
                send_enrollment_confirmation_email(request.user, course, enrollment)
            except Exception as e:
                # Log error but don't fail enrollment
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send enrollment confirmation email: {str(e)}")

            # Send enrollment notification to admin
            try:
                send_enrollment_admin_notification(request.user, course, enrollment)
            except Exception as e:
                # Log error but don't fail enrollment
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send enrollment admin notification: {str(e)}")

            if course.price > 0:
                messages.success(
                    request,
                    f'Successfully enrolled in {course.title}! Your payment has been verified. '
                    f'Check your email for confirmation details.'
                )
            else:
                messages.success(
                    request,
                    f'Successfully enrolled in {course.title}! Check your email for confirmation details.'
                )
        else:
            messages.info(request, f'You are already enrolled in {course.title}.')

        return redirect('courses:course_detail', slug=course_slug)


class ModuleDetailView(LoginRequiredMixin, DetailView):
    """
    Module detail view
    """
    model = Module
    template_name = 'lms/courses/module_detail.html'
    context_object_name = 'module'
    pk_url_kwarg = 'module_id'
    
    def get_object(self):
        course_slug = self.kwargs['course_slug']
        module_id = self.kwargs['module_id']
        return get_object_or_404(
            Module,
            id=module_id,
            course__slug=course_slug,
            is_published=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.object
        
        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=self.request.user,
                course=module.course,
                status='active'
            )
            context['enrollment'] = enrollment
        except Enrollment.DoesNotExist:
            return redirect('courses:course_detail', slug=module.course.slug)
        
        # Get lessons with progress and accessibility
        lessons = module.lessons.filter(is_published=True).order_by('sort_order')
        lesson_data = []
        for lesson in lessons:
            try:
                progress = LessonProgress.objects.get(
                    enrollment=enrollment,
                    lesson=lesson
                )
            except LessonProgress.DoesNotExist:
                progress = None

            # Check lesson accessibility
            is_accessible, access_message = lesson.is_accessible_for_user(self.request.user)

            lesson_data.append({
                'lesson': lesson,
                'progress': progress,
                'is_accessible': is_accessible,
                'access_message': access_message
            })

        context['lesson_data'] = lesson_data
        
        return context


class LessonDetailView(LoginRequiredMixin, DetailView):
    """
    Lesson detail view
    """
    model = Lesson
    template_name = 'lms/courses/lesson_detail.html'
    context_object_name = 'lesson'
    pk_url_kwarg = 'lesson_id'
    
    def get_object(self):
        course_slug = self.kwargs['course_slug']
        lesson_id = self.kwargs['lesson_id']
        return get_object_or_404(
            Lesson,
            id=lesson_id,
            module__course__slug=course_slug,
            is_published=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.object

        # Check enrollment
        try:
            enrollment = Enrollment.objects.get(
                student=self.request.user,
                course=lesson.module.course,
                status='active'
            )
            context['enrollment'] = enrollment
        except Enrollment.DoesNotExist:
            return redirect('courses:course_detail', slug=lesson.module.course.slug)

        # Check if lesson is accessible (prerequisite validation)
        is_accessible, access_message = lesson.is_accessible_for_user(self.request.user)
        context['is_accessible'] = is_accessible
        context['access_message'] = access_message

        if not is_accessible:
            # If lesson is not accessible, don't mark as started or update access time
            context['progress'] = None
            context['next_lesson'] = lesson.get_next_lesson()
            context['prev_lesson'] = lesson.get_previous_lesson()
            return context

        # Get or create lesson progress
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )

        # Mark as started if not already
        if progress.status == 'not_started':
            progress.mark_started()

        # Update last accessed
        enrollment.mark_as_accessed()

        context['progress'] = progress

        # Get next and previous lessons using the new methods
        context['next_lesson'] = lesson.get_next_lesson()
        context['prev_lesson'] = lesson.get_previous_lesson()

        # Check accessibility of next lesson for UI purposes
        next_lesson = context['next_lesson']
        if next_lesson:
            next_accessible, _ = next_lesson.is_accessible_for_user(self.request.user)
            context['next_lesson_accessible'] = next_accessible
        else:
            context['next_lesson_accessible'] = False

        return context
    
    def post(self, request, course_slug, lesson_id):
        """
        Handle lesson completion
        """
        lesson = self.get_object()
        
        try:
            enrollment = Enrollment.objects.get(
                student=request.user,
                course=lesson.module.course,
                status='active'
            )
        except Enrollment.DoesNotExist:
            return JsonResponse({'error': 'Not enrolled'}, status=400)
        
        # Get lesson progress
        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson
        )
        
        # Mark as completed
        if progress.status != 'completed':
            progress.mark_completed()
            return JsonResponse({'status': 'completed', 'message': 'Lesson completed!'})
        
        return JsonResponse({'status': 'already_completed'})


class MyCoursesView(LoginRequiredMixin, ListView):
    """
    User's enrolled courses view
    """
    template_name = 'lms/courses/my_courses.html'
    context_object_name = 'enrollments'
    
    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user
        ).select_related('course').order_by('-enrollment_date')


class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Enhanced user profile view with comprehensive LMS analytics
    """
    template_name = 'lms/courses/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get or create user profile
        try:
            profile = user.profile
        except:
            from users.models import Profile
            profile, created = Profile.objects.get_or_create(user=user)
        context['profile'] = profile

        # Get user enrollments with related data
        enrollments = Enrollment.objects.filter(student=user).select_related('course').prefetch_related('lesson_progress')
        context['enrollments'] = enrollments

        # Basic statistics
        context['total_enrollments'] = enrollments.count()
        context['completed_courses'] = enrollments.filter(status='completed').count()
        context['active_courses'] = enrollments.filter(status='active').count()
        context['dropped_courses'] = enrollments.filter(status='dropped').count()

        # Learning analytics
        from progress.models import Achievement, StudySession, LessonProgress
        from django.db.models import Sum, Avg, Count
        from datetime import datetime, timedelta

        # Total learning time from lesson progress
        total_time_seconds = LessonProgress.objects.filter(
            enrollment__student=user
        ).aggregate(total_time=Sum('time_spent'))['total_time'] or 0
        context['total_learning_hours'] = round(total_time_seconds / 3600, 1)

        # Study sessions analytics
        study_sessions = StudySession.objects.filter(student=user)
        context['total_study_sessions'] = study_sessions.count()

        # Learning streak calculation (consecutive days with activity)
        recent_activity = LessonProgress.objects.filter(
            enrollment__student=user,
            completed_at__isnull=False
        ).order_by('-completed_at')

        learning_streak = self.calculate_learning_streak(recent_activity)
        context['learning_streak'] = learning_streak

        # Recent achievements
        recent_achievements = Achievement.objects.filter(student=user).order_by('-earned_at')[:5]
        context['recent_achievements'] = recent_achievements
        context['total_achievements'] = Achievement.objects.filter(student=user).count()

        # Course progress details for enrolled courses
        course_progress = []
        for enrollment in enrollments:
            progress_data = {
                'enrollment': enrollment,
                'course': enrollment.course,
                'progress_percentage': enrollment.progress_percentage,
                'total_lessons': enrollment.course.total_lessons,
                'completed_lessons': enrollment.lesson_progress.filter(status='completed').count(),
                'last_accessed': enrollment.last_accessed,
                'can_continue': enrollment.lesson_progress.filter(status__in=['not_started', 'in_progress']).exists(),
                'next_lesson': enrollment.lesson_progress.filter(status__in=['not_started', 'in_progress']).first(),
            }
            course_progress.append(progress_data)
        context['course_progress'] = course_progress

        # Payment history (mock data for now - can be enhanced with actual payment records)
        context['payment_history'] = self.get_payment_history(user)

        # Recent activity
        context['recent_activity'] = self.get_recent_activity(user)

        return context

    def calculate_learning_streak(self, recent_activity):
        """Calculate consecutive days of learning activity"""
        if not recent_activity.exists():
            return 0

        from datetime import date, timedelta
        today = date.today()
        streak = 0
        current_date = today

        # Group activities by date
        activity_dates = set()
        for activity in recent_activity:
            activity_dates.add(activity.completed_at.date())

        # Count consecutive days backwards from today
        while current_date in activity_dates:
            streak += 1
            current_date -= timedelta(days=1)

        return streak

    def get_payment_history(self, user):
        """Get user's payment history"""
        # This is a placeholder - can be enhanced with actual payment records
        payment_history = []
        if hasattr(user, 'profile') and user.profile.payment_confirmed_at:
            payment_history.append({
                'date': user.profile.payment_confirmed_at,
                'amount': user.profile.payment_amount or 0,
                'method': user.profile.get_payment_method_display() if user.profile.payment_method else 'N/A',
                'reference': user.profile.payment_reference or 'N/A',
                'status': 'Confirmed'
            })
        return payment_history

    def get_recent_activity(self, user):
        """Get user's recent learning activity"""
        from progress.models import LessonProgress
        recent_progress = LessonProgress.objects.filter(
            enrollment__student=user
        ).select_related('lesson', 'enrollment__course').order_by('-completed_at')[:10]

        activities = []
        for progress in recent_progress:
            if progress.completed_at:
                activities.append({
                    'type': 'lesson_completed',
                    'title': f"Completed: {progress.lesson.title}",
                    'course': progress.enrollment.course.title,
                    'date': progress.completed_at,
                    'icon': 'fas fa-check-circle',
                    'color': 'success'
                })
            elif progress.started_at:
                activities.append({
                    'type': 'lesson_started',
                    'title': f"Started: {progress.lesson.title}",
                    'course': progress.enrollment.course.title,
                    'date': progress.started_at,
                    'icon': 'fas fa-play-circle',
                    'color': 'info'
                })

        return activities[:5]  # Return only 5 most recent


class HowItWorksView(TemplateView):
    """
    How It Works information page for YITP administrators
    """
    template_name = 'lms/courses/how_it_works.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add statistics for the overview
        context['total_courses'] = Course.objects.filter(is_published=True).count()
        context['total_categories'] = Category.objects.filter(is_active=True).count()
        context['total_students'] = User.objects.filter(is_active=True).count()

        # Sample course categories for demonstration
        context['sample_categories'] = Category.objects.filter(is_active=True)[:6]

        return context


class AdminSupportView(TemplateView):
    """
    Admin Support page - comprehensive guide for system administrators
    """
    template_name = 'lms/courses/admin_support.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # System statistics for overview
        context['total_courses'] = Course.objects.filter(is_published=True).count()
        context['total_categories'] = Category.objects.filter(is_active=True).count()
        context['total_students'] = User.objects.filter(is_active=True).count()
        context['total_instructors'] = User.objects.filter(is_active=True, groups__name='Instructors').count()

        # Recent activity statistics
        from django.utils import timezone
        from datetime import timedelta

        last_30_days = timezone.now() - timedelta(days=30)
        context['recent_enrollments'] = Enrollment.objects.filter(enrollment_date__gte=last_30_days).count()
        context['active_enrollments'] = Enrollment.objects.filter(status='active').count()
        context['completed_courses'] = Enrollment.objects.filter(status='completed').count()

        # Course categories for demonstration
        context['sample_categories'] = Category.objects.filter(is_active=True)[:8]

        return context

