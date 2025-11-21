from pathlib import Path

from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse
from .models import Course, Category, Module, Lesson
from progress.models import Enrollment, LessonProgress
from users.email_utils import send_enrollment_confirmation_email, send_enrollment_admin_notification


User = get_user_model()


def normalize_lesson_resources(resource_items):
    """Flatten and normalize lesson resource entries for safe rendering"""
    normalized = []

    def build_entry(entry):
        if entry is None:
            return
        label = ''
        description = ''
        details = ''
        url = ''

        if isinstance(entry, dict):
            label = entry.get('label') or entry.get('title') or entry.get('name') or entry.get('text')
            description = entry.get('description') or entry.get('summary')
            details = entry.get('details') or entry.get('notes')
            url = entry.get('url') or entry.get('link') or entry.get('href') or entry.get('src')
        else:
            label = str(entry)
            if isinstance(entry, str) and entry.startswith(('http://', 'https://')):
                url = entry

        if not label and url:
            label = url

        if label or url or description:
            normalized.append({
                'label': label or 'Additional Resource',
                'description': description,
                'details': details,
                'url': url,
            })

    if not resource_items:
        return normalized

    for item in resource_items:
        if isinstance(item, dict) and isinstance(item.get('external_links'), list):
            for nested in item['external_links']:
                build_entry(nested)
        else:
            build_entry(item)

    return normalized


def get_module2_pdf_path(sort_order):
    """Return relative static path to Module 2 PDF matching the sort order."""
    pdf_dir = Path(settings.BASE_DIR) / 'static' / 'module2' / 'pdf'
    if not pdf_dir.exists():
        return None

    pattern = f"*Lesson {sort_order}_*.pdf"
    match = next(pdf_dir.glob(pattern), None)
    if not match:
        return None

    try:
        rel_path = match.relative_to(Path(settings.BASE_DIR) / 'static')
    except ValueError:
        rel_path = match.name
    return str(rel_path).replace('\\', '/')


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

        # Get user certificates
        try:
            from certificates.certificate_service import CertificateService
            user_certificates = CertificateService.get_user_certificates(user)
            context['user_certificates'] = user_certificates
        except ImportError:
            # Fallback if certificate service is not available
            from progress.models import Certificate
            user_certificates = Certificate.objects.filter(enrollment__student=user)
            context['user_certificates'] = user_certificates

        return context


class Module2DownloadView(LoginRequiredMixin, TemplateView):
    """Temporary hub to open Module 2 lessons directly (no iframe)."""
    template_name = 'lms/courses/module2fordownload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module_dir = Path(settings.BASE_DIR) / 'static' / 'module2'
        lessons = []

        def sort_key(path_obj):
            try:
                return int(path_obj.stem.split('_')[-1])
            except Exception:
                return path_obj.stem

        if module_dir.exists():
            for html_file in sorted(module_dir.glob('lesson_*.html'), key=sort_key):
                stem = html_file.stem
                number = stem.split('_')[-1]
                pdf_rel = get_module2_pdf_path(number)
                lessons.append({
                    'number': number,
                    'title': f'Lesson {number}',
                    'html_path': f'module2/{html_file.name}',
                    'pdf_path': pdf_rel,
                })

        context['module2_lessons'] = lessons
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
        
        return queryset.order_by('created_at')  # Oldest first
    
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

        # Optimized query: Get all modules with lessons (excluding heavy content fields)
        from django.db.models import Prefetch

        # Create optimized lesson queryset that excludes heavy content fields
        lesson_queryset = Lesson.objects.filter(is_published=True).defer(
            'content',  # Exclude heavy HTML content
            'learning_objectives',  # Exclude large text fields
            'resources'  # Exclude JSON field
        ).order_by('sort_order')

        modules = course.modules.filter(is_published=True).prefetch_related(
            Prefetch('lessons', queryset=lesson_queryset)
        ).order_by('sort_order')

        # Get all lesson progress for this enrollment in one query (if enrolled)
        all_lesson_progress = {}
        enrollment = None
        if self.request.user.is_authenticated:
            try:
                enrollment = Enrollment.objects.get(
                    student=self.request.user,
                    course=course,
                    status__in=['active', 'completed']
                )

                # Pre-fetch ALL lesson progress in a single query
                progress_queryset = LessonProgress.objects.filter(
                    enrollment=enrollment
                ).select_related('lesson')
                for progress in progress_queryset:
                    all_lesson_progress[progress.lesson_id] = progress

            except Enrollment.DoesNotExist:
                pass

        # Pre-compute lesson sequence to avoid N+1 queries in accessibility checks
        all_lessons_ordered = []
        for module in modules:
            module_lessons = [lesson for lesson in module.lessons.all() if lesson.is_published]
            all_lessons_ordered.extend(module_lessons)

        # Create lesson sequence mapping for efficient lookups
        lesson_sequence = {lesson.id: i for i, lesson in enumerate(all_lessons_ordered)}

        # Process modules and lessons with pre-fetched data
        for module in modules:
            lessons = [lesson for lesson in module.lessons.all() if lesson.is_published]
            lesson_data = []

            for lesson in lessons:
                # Get progress from pre-fetched data
                progress = all_lesson_progress.get(lesson.id)

                # Check accessibility efficiently without additional queries
                is_accessible = self._check_lesson_accessibility_optimized(
                    lesson, enrollment, all_lesson_progress, all_lessons_ordered, lesson_sequence
                )

                lesson_data.append({
                    'lesson': lesson,
                    'progress': progress,
                    'is_accessible': is_accessible
                })

            module.lesson_data = lesson_data

        context['modules'] = modules
        context['enrollment'] = enrollment
        context['is_enrolled'] = enrollment is not None

        # Calculate course statistics efficiently using already-fetched data
        context['total_modules'] = len(modules)
        context['total_lessons'] = sum(len(module.lessons.all()) for module in modules)

        # Single optimized query for enrollment count
        context['enrolled_count'] = course.enrollments.filter(
            status__in=['active', 'completed']
        ).count()

        # Calculate average rating from course reviews
        from django.db.models import Avg
        reviews = course.reviews.filter(is_published=True)
        if reviews.exists():
            avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
            context['average_rating'] = round(avg_rating, 1) if avg_rating else 0
            context['rating_count'] = reviews.count()
        else:
            context['average_rating'] = 0
            context['rating_count'] = 0

        return context

    def _check_lesson_accessibility_optimized(self, lesson, enrollment, all_lesson_progress, all_lessons_ordered, lesson_sequence):
        """
        Efficiently check lesson accessibility using pre-computed lesson sequence
        """
        if not enrollment:
            return False

        # Check trial access boundaries first
        from .trial_service import TrialAccessService
        try:
            trial_access = TrialAccessService.can_access_lesson(self.request.user, lesson)
            if trial_access['is_trial_user']:
                if not trial_access['can_access']:
                    return False
        except Exception:
            # If trial service fails, continue with normal checks
            pass

        # First lesson is always accessible (if within trial boundaries)
        lesson_index = lesson_sequence.get(lesson.id)
        if lesson_index == 0:
            return True

        # Check if previous lesson is completed using pre-fetched data
        if lesson_index and lesson_index > 0:
            previous_lesson = all_lessons_ordered[lesson_index - 1]
            prev_progress = all_lesson_progress.get(previous_lesson.id)
            if not prev_progress or prev_progress.status != 'completed':
                return False

        return True

    def _should_offer_trial_access(self, course):
        """
        Determine if trial access should be offered for this course

        Trial access rules:
        - All courses should offer free trial access by default (paid and free courses)
        - Exception: Courses with only one module/unit OR only one lesson should NOT have trial access
        """
        # Check if course has sufficient content for trial
        total_modules = course.total_modules
        total_lessons = course.total_lessons

        # If course has only one module OR only one lesson, no trial
        if total_modules <= 1 or total_lessons <= 1:
            return False

        return True

    def _get_trial_unavailable_reason(self, course):
        """
        Get the reason why trial access is not available
        """
        total_modules = course.total_modules
        total_lessons = course.total_lessons

        if total_modules <= 1:
            return f"Trial not available - This course contains only one module. Full access required."
        elif total_lessons <= 1:
            return f"Trial not available - This course contains only one lesson. Full access required."

        return None


class EnrollView(LoginRequiredMixin, View):
    """
    Unified course enrollment view using EnrollmentService
    """
    def post(self, request, course_slug):
        from .enrollment_service import EnrollmentService

        # Get course using the service
        try:
            course = EnrollmentService.get_course_by_slug_or_id(course_slug)
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
                status__in=['active', 'completed']
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
    Lesson detail view with Module 2 template detection
    """
    model = Lesson
    context_object_name = 'lesson'
    pk_url_kwarg = 'lesson_id'

    def get_template_names(self):
        """
        Determine which template to use based on lesson module
        """
        lesson = self.get_object()

        # Check if this is Module 2 (Personal Initiative)
        if lesson.module and 'Personal Initiative' in lesson.module.title:
            return ['lms/courses/lesson_detail_module2main.html']

        # Default template for all other modules
        return ['lms/courses/lesson_detail.html']
    
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
                status__in=['active', 'completed']
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

        # Add quiz status information
        from assessments.services import QuizValidationService
        quiz_status = QuizValidationService.get_user_quiz_status(self.request.user, lesson)
        context['quiz_status'] = quiz_status

        context['normalized_resources'] = normalize_lesson_resources(lesson.resources)
        if lesson.module and 'Personal Initiative' in lesson.module.title:
            pdf_rel = get_module2_pdf_path(lesson.sort_order)
            context['module2_pdf_path'] = pdf_rel
            context['module2_pdf_available'] = bool(pdf_rel)
        else:
            context['module2_pdf_available'] = False
            context['module2_pdf_path'] = None

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


class LessonCompleteView(LoginRequiredMixin, View):
    """
    Dedicated view for handling lesson completion via AJAX with quiz validation
    """

    def post(self, request, course_slug, lesson_id):
        """
        Mark lesson as complete and return updated status with quiz validation
        """
        try:
            # Get the lesson
            lesson = get_object_or_404(
                Lesson,
                id=lesson_id,
                module__course__slug=course_slug,
                is_published=True
            )

            # Check enrollment
            try:
                enrollment = Enrollment.objects.get(
                    student=request.user,
                    course=lesson.module.course,
                    status='active'
                )
            except Enrollment.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'You are not enrolled in this course.'
                }, status=403)

            # Check if lesson is accessible
            is_accessible, access_message = lesson.is_accessible_for_user(request.user)
            if not is_accessible:
                return JsonResponse({
                    'success': False,
                    'error': access_message
                }, status=403)

            # Import quiz validation service
            from assessments.services import QuizValidationService

            # Validate quiz requirements before allowing completion
            can_complete, validation_message, quiz_data = QuizValidationService.validate_lesson_completion(
                request.user, lesson
            )

            if not can_complete:
                return JsonResponse({
                    'success': False,
                    'requires_quiz': True,
                    'quiz_data': quiz_data,
                    'message': validation_message
                })

            # Get or create lesson progress
            progress, created = LessonProgress.objects.get_or_create(
                enrollment=enrollment,
                lesson=lesson
            )

            # Mark as completed if not already
            if progress.status != 'completed':
                progress.mark_completed()

                # Award points and check for achievements using gamification service
                from progress.services import GamificationService
                gamification_result = GamificationService.award_lesson_completion_points(
                    request.user, lesson
                )

                # Get updated enrollment progress
                enrollment.refresh_from_db()

                # Check if next lesson is now accessible
                next_lesson = lesson.get_next_lesson()
                next_lesson_accessible = False
                next_lesson_url = None

                if next_lesson:
                    next_accessible, _ = next_lesson.is_accessible_for_user(request.user)
                    next_lesson_accessible = next_accessible
                    if next_accessible:
                        from django.urls import reverse
                        next_lesson_url = reverse('courses:lesson_detail', kwargs={
                            'course_slug': course_slug,
                            'lesson_id': next_lesson.id
                        })

                return JsonResponse({
                    'success': True,
                    'status': 'completed',
                    'message': 'Lesson completed successfully!',
                    'progress_percentage': float(enrollment.progress_percentage),
                    'next_lesson_accessible': next_lesson_accessible,
                    'next_lesson_url': next_lesson_url,
                    'next_lesson_title': next_lesson.title if next_lesson else None,
                    'course_progress': {
                        'completed_lessons': enrollment.lesson_progress.filter(status='completed').count(),
                        'total_lessons': enrollment.course.total_lessons,
                        'percentage': float(enrollment.progress_percentage)
                    },
                    'gamification': {
                        'points_awarded': gamification_result['points_awarded'],
                        'total_points': gamification_result['total_points'],
                        'new_achievements': [
                            {
                                'title': achievement.title,
                                'description': achievement.description,
                                'badge_icon': achievement.badge_icon,
                                'points': achievement.points
                            } for achievement in gamification_result['new_achievements']
                        ],
                        'current_streak': gamification_result['current_streak']
                    }
                })
            else:
                return JsonResponse({
                    'success': True,
                    'status': 'already_completed',
                    'message': 'Lesson was already completed.'
                })

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error completing lesson {lesson_id} for user {request.user.id}: {str(e)}")

            return JsonResponse({
                'success': False,
                'error': 'An error occurred while completing the lesson. Please try again.'
            }, status=500)


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

    def post(self, request, *args, **kwargs):
        """
        Handle account settings actions (e.g., delete account request)
        """
        action = request.POST.get('action')
        if action == 'request_delete':
            reason = request.POST.get('reason', '').strip()
            try:
                from django.core.mail import send_mail
                from django.conf import settings

                admin_email = getattr(settings, 'ADMIN_EMAIL', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
                if not admin_email:
                    admin_email = 'info@youthimpactglobal.com'

                subject = f"Account deletion request from {request.user.email}"
                message = (
                    f"User: {request.user.get_full_name() or request.user.username}\n"
                    f"Email: {request.user.email}\n"
                    f"Reason: {reason or 'No reason provided'}\n"
                )
                send_mail(subject, message, admin_email, [admin_email], fail_silently=True)
                messages.success(request, "Your account deletion request has been sent to admin. We'll reach out shortly.")
            except Exception:
                messages.error(request, "Could not send the deletion request. Please contact support.")

        return redirect('profile')

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
