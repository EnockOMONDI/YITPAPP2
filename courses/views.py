from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from .models import Course, Category, Module, Lesson
from progress.models import Enrollment, LessonProgress


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
        except UserProfile.DoesNotExist:
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
        
        # Check if already enrolled
        enrollment, created = Enrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'status': 'active'}
        )
        
        if created:
            messages.success(request, f'Successfully enrolled in {course.title}!')
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
        
        # Get lessons with progress
        lessons = module.lessons.filter(is_published=True)
        lesson_progress = {}
        for lesson in lessons:
            try:
                progress = LessonProgress.objects.get(
                    enrollment=enrollment,
                    lesson=lesson
                )
                lesson_progress[lesson.id] = progress
            except LessonProgress.DoesNotExist:
                lesson_progress[lesson.id] = None
        
        context['lessons'] = lessons
        context['lesson_progress'] = lesson_progress
        
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
        
        # Get next and previous lessons
        current_order = lesson.sort_order
        module = lesson.module
        
        next_lesson = module.lessons.filter(
            sort_order__gt=current_order,
            is_published=True
        ).first()
        
        prev_lesson = module.lessons.filter(
            sort_order__lt=current_order,
            is_published=True
        ).last()
        
        context['next_lesson'] = next_lesson
        context['prev_lesson'] = prev_lesson
        
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
    User profile view
    """
    template_name = 'lms/courses/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        context['profile'] = profile

        # Get user statistics
        enrollments = Enrollment.objects.filter(student=user)
        context['total_enrollments'] = enrollments.count()
        context['completed_courses'] = enrollments.filter(status='completed').count()
        context['active_courses'] = enrollments.filter(status='active').count()

        # Get recent achievements
        from progress.models import Achievement
        recent_achievements = Achievement.objects.filter(student=user).order_by('-earned_at')[:5]
        context['recent_achievements'] = recent_achievements

        return context


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

