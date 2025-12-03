"""
Instructor-specific views for enhanced instructor experience
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Avg, Sum, Prefetch
from django.templatetags.static import static
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

User = get_user_model()

from courses.models import Course, Module, Lesson
from assessments.models import Quiz
from progress.models import QuizAttempt, Enrollment, LessonProgress
from communication.models import Message, Notification
from payments.models import Payment
from .models import InstructorProfile, SponsorshipRequest, ModuleInstructor
from .forms import (
    InstructorModuleForm,
    InstructorLessonForm,
    InstructorQuizForm,
    InstructorQuestionForm,
)


class InstructorRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is a verified instructor"""
    allowed_roles = None
    
    def test_func(self):
        try:
            instructor_profile = self.request.user.instructor_profile
            role_allowed = True
            if self.allowed_roles:
                role_allowed = instructor_profile.instructor_role in self.allowed_roles
            return instructor_profile.is_verified and instructor_profile.is_active and role_allowed
        except:
            return False
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, "Please log in to access the instructor dashboard.")
            return redirect('login')
        else:
            messages.error(self.request, "You need to be a verified instructor to access this page.")
            return redirect('profile')


class InstructorDashboardView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """Branded module manager dashboard for instructors."""
    template_name = 'instructor/dashboard.html'

    def _get_assigned_modules(self, instructor_profile):
        base_qs = Module.objects.select_related('course', 'course__instructor').prefetch_related(
            Prefetch(
                'lessons',
                queryset=Lesson.objects.order_by('sort_order').prefetch_related('quizzes')
            ),
            'module_instructors__instructor'
        )

        if instructor_profile.instructor_role == 'system_admin':
            return list(base_qs)

        return list(
            base_qs.filter(
                module_instructors__instructor=self.request.user,
                module_instructors__is_active=True
            ).distinct()
        )

    def _get_assignment_map(self, modules):
        if not modules:
            return {}
        assignments = ModuleInstructor.objects.filter(
            module__in=modules,
            instructor=self.request.user,
            is_active=True
        )
        return {assignment.module_id: assignment for assignment in assignments}

    def _is_static_module(self, module):
        static_ids = getattr(settings, 'STATIC_MODULE_IDS', [])
        static_markers = getattr(settings, 'STATIC_MODULE_TITLES', ['module 2'])
        if module.id in static_ids:
            return True
        title = (module.title or '').lower()
        return any(marker.lower() in title for marker in static_markers)

    def _get_selected_module(self, modules):
        if not modules:
            return None
        requested_id = self.request.GET.get('module_id') or self.request.POST.get('module_id')
        if requested_id:
            for module in modules:
                if str(module.id) == str(requested_id):
                    return module
        return modules[0]

    def _module_capabilities(self, assignment_map, module):
        profile = self.request.user.instructor_profile
        if profile.instructor_role == 'system_admin':
            return {
                'can_edit_content': True,
                'can_manage_enrollments': True,
                'can_grade_assessments': True,
            }

        assignment = assignment_map.get(module.id) if module else None
        return {
            'can_edit_content': bool(assignment and assignment.can_edit_content),
            'can_manage_enrollments': bool(assignment and assignment.can_manage_enrollments),
            'can_grade_assessments': bool(assignment and assignment.can_grade_assessments),
        }

    def _redirect_with_module(self, module):
        from django.urls import reverse
        if not module:
            return redirect('users:instructor_dashboard')
        return redirect(f"{reverse('users:instructor_dashboard')}?module_id={module.id}")

    def post(self, request, *args, **kwargs):
        instructor_profile = request.user.instructor_profile
        assigned_modules = self._get_assigned_modules(instructor_profile)
        selected_module = self._get_selected_module(assigned_modules)
        assignment_map = self._get_assignment_map(assigned_modules)

        if not selected_module:
            messages.error(request, "No modules are assigned to your instructor profile yet.")
            return redirect('users:instructor_dashboard')

        action = request.POST.get('action')
        form_store = {}

        if action == 'update_module':
            if self._is_static_module(selected_module):
                messages.warning(request, "This module is static content. Please contact a super admin for structural updates.")
                return self._redirect_with_module(selected_module)

            if not self._module_capabilities(assignment_map, selected_module)['can_edit_content']:
                messages.error(request, "You do not have permission to edit this module.")
                return self._redirect_with_module(selected_module)

            module_form = InstructorModuleForm(request.POST, instance=selected_module)
            if module_form.is_valid():
                module_form.save()
                messages.success(request, f"Module '{selected_module.title}' updated successfully.")
                return self._redirect_with_module(selected_module)
            form_store['module_form'] = module_form

        elif action == 'create_lesson':
            capabilities = self._module_capabilities(assignment_map, selected_module)
            if not capabilities['can_edit_content'] or self._is_static_module(selected_module):
                messages.error(request, "You cannot add lessons to this module.")
                return self._redirect_with_module(selected_module)

            lesson_form = InstructorLessonForm(request.POST)
            if lesson_form.is_valid():
                lesson = lesson_form.save(commit=False)
                lesson.module = selected_module
                lesson.save()
                messages.success(request, f"Lesson '{lesson.title}' created successfully.")
                return self._redirect_with_module(selected_module)
            form_store['lesson_form'] = lesson_form

        elif action == 'create_quiz':
            lesson_queryset = selected_module.lessons.all()
            quiz_form = InstructorQuizForm(request.POST, lesson_queryset=lesson_queryset)
            if not self._module_capabilities(assignment_map, selected_module)['can_grade_assessments']:
                messages.error(request, "You do not have permission to manage quizzes for this module.")
                return self._redirect_with_module(selected_module)

            if quiz_form.is_valid():
                quiz_form.save()
                messages.success(request, "Quiz created successfully.")
                return self._redirect_with_module(selected_module)
            form_store['quiz_form'] = quiz_form
        elif action == 'create_question':
            quiz_queryset = Quiz.objects.filter(lesson__module=selected_module)
            question_form = InstructorQuestionForm(request.POST, quiz_queryset=quiz_queryset)
            if not self._module_capabilities(assignment_map, selected_module)['can_grade_assessments']:
                messages.error(request, "You do not have permission to add questions for this module.")
                return self._redirect_with_module(selected_module)
            if question_form.is_valid():
                question_form.save()
                messages.success(request, "Question added to quiz successfully.")
                return self._redirect_with_module(selected_module)
            form_store['question_form'] = question_form

        self.dashboard_forms = form_store
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = self.request.user
        instructor_profile = instructor.instructor_profile

        assigned_modules = self._get_assigned_modules(instructor_profile)
        selected_module = self._get_selected_module(assigned_modules)
        assignment_map = self._get_assignment_map(assigned_modules)

        instructor_courses = list({module.course for module in assigned_modules})

        # Enrollment and analytics data
        course_ids = [course.id for course in instructor_courses if course]
        enrollment_map = defaultdict(list)
        if course_ids:
            for enrollment in Enrollment.objects.filter(course_id__in=course_ids).select_related('student', 'course').order_by('-enrollment_date'):
                enrollment_map[enrollment.course_id].append(enrollment)

        total_students = sum(1 for course_id in enrollment_map for _ in enrollment_map[course_id])
        total_courses = len(instructor_courses)
        published_courses = len([course for course in instructor_courses if course and course.is_published])
        module_count = len(assigned_modules)
        published_modules = len([module for module in assigned_modules if module.is_published])

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_enrollments = sum(
            1 for course_id in enrollment_map for enrollment in enrollment_map[course_id]
            if enrollment.enrollment_date >= thirty_days_ago
        )

        quiz_attempts = QuizAttempt.objects.filter(
            quiz__lesson__module__in=assigned_modules,
            completed_at__gte=thirty_days_ago
        )
        avg_quiz_score = quiz_attempts.aggregate(avg_score=Avg('score'))['avg_score'] or 0

        recent_messages = Message.objects.filter(
            recipient=instructor
        ).order_by('-sent_at')[:5]
        unread_messages_count = Message.objects.filter(
            recipient=instructor,
            is_read=False
        ).count()

        recent_lessons = Lesson.objects.filter(
            module__in=assigned_modules
        ).select_related('module', 'module__course').order_by('-updated_at')[:6]
        recent_quizzes = Quiz.objects.filter(
            lesson__module__in=assigned_modules
        ).select_related('lesson', 'lesson__module').order_by('-created_at')[:4]

        recent_progress = list(
            LessonProgress.objects.filter(
                lesson__module__in=assigned_modules
            ).select_related('lesson', 'enrollment__student').order_by('-completed_at', '-started_at')[:6]
        )
        for progress in recent_progress:
            student = getattr(getattr(progress, 'enrollment', None), 'student', None)
            if student:
                full_name = (student.get_full_name() or '').strip()
                progress.student_display_name = full_name or student.username
            else:
                progress.student_display_name = "Unknown student"

        module_cards = []
        for module in assigned_modules:
            lessons = list(module.lessons.all())
            published_lessons = len([lesson for lesson in lessons if lesson.is_published])
            quizzes_count = sum(lesson.quizzes.count() for lesson in lessons)
            enrollments = enrollment_map.get(module.course_id, [])
            avg_progress = 0
            if enrollments:
                avg_progress = sum(float(enrollment.progress_percentage) for enrollment in enrollments) / len(enrollments)
            module_cards.append({
                'module': module,
                'lessons': len(lessons),
                'published_lessons': published_lessons,
                'quizzes': quizzes_count,
                'students': len(enrollments),
                'avg_progress': round(avg_progress, 1),
                'is_static': self._is_static_module(module),
                'assignment': assignment_map.get(module.id),
            })

        selected_module_lessons = selected_module.lessons.all() if selected_module else Lesson.objects.none()
        selected_module_quizzes = Quiz.objects.filter(lesson__module=selected_module).select_related('lesson') if selected_module else Quiz.objects.none()
        selected_module_students = enrollment_map.get(selected_module.course_id, [])[:6] if selected_module else []
        selected_module_progress = LessonProgress.objects.filter(
            lesson__module=selected_module
        ).select_related('lesson', 'enrollment__student').order_by('-completed_at', '-started_at')[:6] if selected_module else []

        module_capabilities = self._module_capabilities(assignment_map, selected_module) if selected_module else {
            'can_edit_content': False,
            'can_manage_enrollments': False,
            'can_grade_assessments': False,
        }

        forms_from_post = getattr(self, 'dashboard_forms', {})
        module_form = forms_from_post.get('module_form') or (InstructorModuleForm(instance=selected_module) if selected_module else None)
        lesson_form = forms_from_post.get('lesson_form') or (InstructorLessonForm(initial={
            'sort_order': selected_module.lessons.count() + 1 if selected_module else 0,
            'estimated_duration': selected_module.estimated_duration if selected_module else 30,
        }) if selected_module else None)
        quiz_form = forms_from_post.get('quiz_form') or (InstructorQuizForm(
            lesson_queryset=selected_module.lessons.all()
        ) if selected_module else None)
        quiz_queryset = Quiz.objects.filter(lesson__module=selected_module) if selected_module else Quiz.objects.none()
        question_form = forms_from_post.get('question_form') or (InstructorQuestionForm(
            quiz_queryset=quiz_queryset
        ) if selected_module else None)

        context.update({
            'instructor_profile': instructor_profile,
            'assigned_modules': module_cards,
            'selected_module': selected_module,
            'selected_module_is_static': self._is_static_module(selected_module) if selected_module else False,
            'selected_module_lessons': selected_module_lessons,
            'selected_module_quizzes': selected_module_quizzes,
            'selected_module_students': selected_module_students,
            'selected_module_progress': selected_module_progress,
            'module_capabilities': module_capabilities,
            'module_form': module_form,
            'lesson_form': lesson_form,
            'quiz_form': quiz_form,
            'question_form': question_form,
            'total_students': total_students,
            'total_courses': total_courses,
            'published_courses': published_courses,
            'module_count': module_count,
            'published_modules': published_modules,
            'recent_enrollments': recent_enrollments,
            'avg_quiz_score': round(avg_quiz_score, 1),
            'recent_messages': recent_messages,
            'recent_lessons': recent_lessons,
            'recent_quizzes': recent_quizzes,
            'recent_progress': recent_progress,
            'instructor_courses': instructor_courses[:8],
            'unread_messages_count': unread_messages_count,
        })

        return context


class InstructorCoursesView(LoginRequiredMixin, InstructorRequiredMixin, ListView):
    """List view of instructor's modules with management options"""
    template_name = 'instructor/courses.html'
    context_object_name = 'modules'
    paginate_by = 12
    
    def get_queryset(self):
        instructor = self.request.user
        instructor_profile = instructor.instructor_profile
        
        if instructor_profile.instructor_role == 'system_admin':
            queryset = Module.objects.select_related('course').all()
        else:
            queryset = Module.objects.select_related('course').filter(
                module_instructors__instructor=instructor,
                module_instructors__is_active=True
            ).distinct()
        
        status = self.request.GET.get('status')
        if status == 'published':
            queryset = queryset.filter(is_published=True)
        elif status == 'draft':
            queryset = queryset.filter(is_published=False)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(course__title__icontains=search)
            )
        
        queryset = queryset.annotate(
            lesson_count=Count('lessons', distinct=True),
            quiz_count=Count('lessons__quizzes', distinct=True),
            student_count=Count(
                'course__enrollments',
                filter=Q(course__enrollments__status='active'),
                distinct=True
            ),
        )
        
        return queryset.order_by('course__title', 'sort_order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['unread_messages_count'] = Message.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        
        modules_page = context.get('modules')
        module_cards = []
        if modules_page:
            for module in modules_page:
                course = getattr(module, 'course', None)
                course_title = ((course.title if course else '') or '').strip()
                description = (module.description or '').strip()
                thumbnail_field = getattr(course, 'thumbnail', None)
                thumbnail_url = ''
                if thumbnail_field:
                    url = getattr(thumbnail_field, 'url', None)
                    if url:
                        thumbnail_url = url
                    elif isinstance(thumbnail_field, str):
                        if thumbnail_field.startswith(('http://', 'https://', '/')):
                            thumbnail_url = thumbnail_field
                        else:
                            thumbnail_url = static(thumbnail_field)
                module_cards.append({
                    'module': module,
                    'course_title': course_title or "Untitled Course",
                    'description': description or "No description provided.",
                    'lesson_count': getattr(module, 'lesson_count', None) or module.lessons.count(),
                    'quiz_count': getattr(module, 'quiz_count', 0),
                    'student_count': getattr(module, 'student_count', 0),
                    'thumbnail_url': thumbnail_url,
                })
        context['module_cards'] = module_cards
        return context


class InstructorAnalyticsView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """Detailed analytics view for instructor's courses"""
    template_name = 'instructor/analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = self.request.user
        instructor_profile = instructor.instructor_profile
        
        # Get instructor's courses
        if instructor_profile.instructor_role == 'system_admin':
            instructor_courses = Course.objects.all()
        else:
            instructor_courses = Course.objects.filter(instructor=instructor)
        
        # Time-based analytics
        thirty_days_ago = timezone.now() - timedelta(days=30)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # Enrollment trends
        enrollments_30d = Enrollment.objects.filter(
            course__in=instructor_courses,
            enrollment_date__gte=thirty_days_ago
        ).count()
        
        enrollments_7d = Enrollment.objects.filter(
            course__in=instructor_courses,
            enrollment_date__gte=seven_days_ago
        ).count()
        
        # Quiz performance analytics
        quiz_attempts_30d = QuizAttempt.objects.filter(
            quiz__lesson__module__course__in=instructor_courses,
            completed_at__gte=thirty_days_ago
        )
        
        quiz_pass_rate = quiz_attempts_30d.filter(is_passed=True).count() / max(quiz_attempts_30d.count(), 1) * 100
        
        # Student engagement metrics
        active_students = Enrollment.objects.filter(
            course__in=instructor_courses,
            status='active'
        ).count()
        
        # Course completion rates
        course_completion_data = []
        for course in instructor_courses:
            total_enrollments = course.enrollments.filter(status='active').count()
            if total_enrollments > 0:
                # Calculate completion based on lesson progress
                completed_enrollments = 0
                for enrollment in course.enrollments.filter(status='active'):
                    progress_percentage = enrollment.progress_percentage
                    if progress_percentage >= 100:
                        completed_enrollments += 1
                
                completion_rate = (completed_enrollments / total_enrollments) * 100
                course_completion_data.append({
                    'course': course,
                    'completion_rate': round(completion_rate, 1),
                    'total_enrollments': total_enrollments,
                    'completed_enrollments': completed_enrollments,
                })
        
        # Sort by completion rate
        course_completion_data.sort(key=lambda x: x['completion_rate'], reverse=True)
        
        context.update({
            'enrollments_30d': enrollments_30d,
            'enrollments_7d': enrollments_7d,
            'quiz_pass_rate': round(quiz_pass_rate, 1),
            'active_students': active_students,
            'course_completion_data': course_completion_data[:10],  # Top 10
            'total_courses': instructor_courses.count(),
            'unread_messages_count': Message.objects.filter(
                recipient=self.request.user,
                is_read=False
            ).count(),
        })
        
        return context


class AccountantDashboardView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """Finance-focused dashboard for accountant role"""
    template_name = 'accountant/dashboard.html'
    allowed_roles = ['accountant']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        confirmed_payments = Payment.objects.filter(status='confirmed')
        pending_payments = Payment.objects.filter(status='pending')

        total_confirmed = confirmed_payments.aggregate(total=Sum('amount'))['total'] or 0
        today_total = confirmed_payments.filter(confirmed_at__date=now.date()).aggregate(total=Sum('amount'))['total'] or 0
        week_total = confirmed_payments.filter(confirmed_at__gte=now - timedelta(days=7)).aggregate(total=Sum('amount'))['total'] or 0

        sponsorship_summary = SponsorshipRequest.objects.values('status').annotate(total=Count('id'))
        sponsorship_map = {item['status']: item['total'] for item in sponsorship_summary}

        context.update({
            'total_confirmed_revenue': total_confirmed,
            'today_revenue': today_total,
            'week_revenue': week_total,
            'pending_payments_count': pending_payments.count(),
            'pending_payments': pending_payments.select_related('user', 'course')[:8],
            'recent_payments': Payment.objects.select_related('user', 'course').order_by('-created_at')[:10],
            'sponsorship_counts': sponsorship_map,
            'recent_sponsorships': SponsorshipRequest.objects.select_related('user', 'course').order_by('-created_at')[:6],
        })
        return context


class ContentManagerDashboardView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """Content operations dashboard for content managers"""
    template_name = 'content_manager/dashboard.html'
    allowed_roles = ['content_manager']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_courses = Course.objects.count()
        published_courses = Course.objects.filter(is_published=True).count()
        draft_courses = total_courses - published_courses

        total_modules = Module.objects.count()
        published_modules = Module.objects.filter(is_published=True).count()

        total_lessons = Lesson.objects.count()
        published_lessons = Lesson.objects.filter(is_published=True).count()

        context.update({
            'total_courses': total_courses,
            'published_courses': published_courses,
            'draft_courses': draft_courses,
            'total_modules': total_modules,
            'published_modules': published_modules,
            'total_lessons': total_lessons,
            'published_lessons': published_lessons,
            'recent_courses': Course.objects.order_by('-updated_at')[:6],
            'draft_lessons': Lesson.objects.filter(is_published=False).select_related('module__course').order_by('-updated_at')[:6],
            'recent_updates': Lesson.objects.order_by('-updated_at')[:6],
        })
        return context


class InstructorMessagesView(LoginRequiredMixin, InstructorRequiredMixin, ListView):
    """Instructor message inbox for student communications"""
    template_name = 'instructor/messages.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def get_queryset(self):
        return Message.objects.filter(
            recipient=self.request.user
        ).order_by('-sent_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Count unread messages
        unread_count = Message.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        
        context['unread_count'] = unread_count
        return context


class InstructorStudentsView(LoginRequiredMixin, InstructorRequiredMixin, TemplateView):
    """List view of students enrolled in instructor's modules"""
    template_name = 'instructor/students.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = self.request.user
        instructor_profile = instructor.instructor_profile
        
        # Get all modules assigned to this instructor
        if instructor_profile.instructor_role == 'system_admin':
            assigned_modules = Module.objects.all()
        else:
            assigned_modules = Module.objects.filter(
                module_instructors__instructor=instructor,
                module_instructors__is_active=True
            ).distinct()
        
        # Get all courses for these modules
        course_ids = list(assigned_modules.values_list('course_id', flat=True).distinct())
        
        # Get all enrollments for these courses
        enrollments = Enrollment.objects.filter(
            course_id__in=course_ids,
            status='active'
        ).select_related('student', 'student__profile', 'course')
        
        # Group by student and calculate stats
        student_stats = defaultdict(lambda: {
            'student': None,
            'enrolled_modules': set(),
            'total_progress': [],
            'quiz_scores': [],
            'last_activity': None
        })
        
        for enrollment in enrollments:
            student_id = enrollment.student.id
            student_stats[student_id]['student'] = enrollment.student
            student_stats[student_id]['enrolled_modules'].add(enrollment.course_id)
            student_stats[student_id]['total_progress'].append(float(enrollment.progress_percentage))
            
            # Get last activity
            last_progress = LessonProgress.objects.filter(
                enrollment=enrollment
            ).order_by('-completed_at', '-started_at').first()
            
            if last_progress:
                current_last = student_stats[student_id]['last_activity']
                # Use completed_at if available, otherwise started_at
                activity_time = last_progress.completed_at or last_progress.started_at
                if activity_time and (not current_last or activity_time > current_last):
                    student_stats[student_id]['last_activity'] = activity_time
            
            # Get quiz scores
            quiz_attempts = QuizAttempt.objects.filter(
                student=enrollment.student,
                quiz__lesson__module__course_id=enrollment.course_id
            ).values_list('score', flat=True)
            student_stats[student_id]['quiz_scores'].extend(quiz_attempts)
        
        # Convert to list with calculated averages
        students_list = []
        for student_id, stats in student_stats.items():
            avg_progress = sum(stats['total_progress']) / len(stats['total_progress']) if stats['total_progress'] else 0
            avg_quiz_score = sum(stats['quiz_scores']) / len(stats['quiz_scores']) if stats['quiz_scores'] else None
            student_obj = stats['student']
            if student_obj:
                full_name = (student_obj.get_full_name() or '').strip()
                display_name = full_name or student_obj.username
            else:
                display_name = "Unknown student"
            
            students_list.append({
                'student': student_obj,
                'enrolled_modules': len(stats['enrolled_modules']),
                'avg_progress': round(avg_progress, 1),
                'avg_quiz_score': round(avg_quiz_score, 1) if avg_quiz_score else None,
                'last_activity': stats['last_activity'],
                'display_name': display_name,
            })
        
        # Apply search filter
        search = self.request.GET.get('search')
        if search:
            search_lower = search.lower()
            students_list = [
                s for s in students_list
                if (search_lower in s['display_name'].lower()) or
                   (s['student'] and (
                       search_lower in (s['student'].username or '').lower() or
                       search_lower in (s['student'].email or '').lower()
                   ))
            ]
        
        # Sort by last activity (most recent first)
        from datetime import datetime, timezone as dt_timezone
        students_list.sort(key=lambda x: x['last_activity'] or datetime.min.replace(tzinfo=dt_timezone.utc), reverse=True)
        
        context['students'] = students_list
        context['search_query'] = self.request.GET.get('search', '')
        context['unread_messages_count'] = Message.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        return context


class InstructorStudentDetailView(LoginRequiredMixin, InstructorRequiredMixin, DetailView):
    """Detailed view of a specific student for instructors"""
    model = User
    template_name = 'instructor/student_detail.html'
    context_object_name = 'student'
    pk_url_kwarg = 'student_id'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.get_object()
        full_name = (student.get_full_name() or '').strip()
        display_name = full_name or student.username
        profile = getattr(student, 'profile', None)
        phone_number = getattr(profile, 'phone_number', '') if profile else ''
        instructor = self.request.user
        instructor_profile = instructor.instructor_profile
        
        # Get instructor's modules
        if instructor_profile.instructor_role == 'system_admin':
            assigned_modules = Module.objects.all()
        else:
            assigned_modules = Module.objects.filter(
                module_instructors__instructor=instructor,
                module_instructors__is_active=True
            ).distinct()
        
        course_ids = list(assigned_modules.values_list('course_id', flat=True).distinct())
        
        # Get student's enrollments in instructor's courses
        enrollments = Enrollment.objects.filter(
            student=student,
            course_id__in=course_ids
        ).select_related('course').prefetch_related('lesson_progress')
        
        # Calculate stats
        total_progress = []
        quiz_scores = []
        completed_lessons = 0
        total_lessons = 0
        
        for enrollment in enrollments:
            total_progress.append(float(enrollment.progress_percentage))
            completed_lessons += enrollment.lesson_progress.filter(status='completed').count()
            total_lessons += enrollment.course.total_lessons or 0
            
            # Get quiz scores for this enrollment
            quiz_attempts = QuizAttempt.objects.filter(
                student=student,
                quiz__lesson__module__course=enrollment.course
            ).values_list('score', flat=True)
            quiz_scores.extend(quiz_attempts)
        
        overall_progress = sum(total_progress) / len(total_progress) if total_progress else 0
        avg_quiz_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else None
        
        # Get total study time
        total_time_seconds = LessonProgress.objects.filter(
            enrollment__student=student,
            enrollment__course_id__in=course_ids
        ).aggregate(total=Sum('time_spent'))['total'] or 0
        total_study_hours = round(total_time_seconds / 3600, 1)
        
        # Get last activity
        last_activity = LessonProgress.objects.filter(
            enrollment__student=student,
            enrollment__course_id__in=course_ids
        ).order_by('-completed_at', '-started_at').first()
        
        last_activity_time = None
        if last_activity:
            last_activity_time = last_activity.completed_at or last_activity.started_at
        
        # Get recent activities
        recent_progress = LessonProgress.objects.filter(
            enrollment__student=student,
            enrollment__course_id__in=course_ids
        ).select_related('lesson').order_by('-completed_at', '-started_at')[:10]
        
        recent_activities = []
        for progress in recent_progress:
            if progress.completed_at:
                recent_activities.append({
                    'type': 'lesson_completed',
                    'title': f"Completed: {progress.lesson.title}",
                    'date': progress.completed_at
                })
            elif progress.started_at:
                recent_activities.append({
                    'type': 'lesson_started',
                    'title': f"Started: {progress.lesson.title}",
                    'date': progress.started_at
                })
        
        # Add enrollment details
        enriched_enrollments = []
        for enrollment in enrollments:
            enrollment_date_display = "N/A"
            if enrollment.enrollment_date:
                local_date = timezone.localtime(enrollment.enrollment_date)
                enrollment_date_display = local_date.strftime("%b %d, %Y")
            completed_count = enrollment.lesson_progress.filter(status='completed').count()
            total_course_lessons = enrollment.course.total_lessons or 0
            progress_value = float(enrollment.progress_percentage)
            enriched_enrollments.append({
                'course_title': (enrollment.course.title or '').strip() or "Untitled Module",
                'enrollment_date_display': enrollment_date_display,
                'progress_value': progress_value,
                'progress_display': f"{progress_value:.2f}%",
                'status_display': enrollment.get_status_display(),
                'status_badge_class': self._status_badge_class(enrollment.status),
                'lessons_display': f"{completed_count}/{total_course_lessons or '—'}",
                'completed_lessons': completed_count,
                'total_lessons': total_course_lessons,
            })
    
        context.update({
            'enrollments': enriched_enrollments,
            'enrolled_modules_count': enrollments.count(),
            'overall_progress': round(overall_progress, 1),
            'avg_quiz_score': round(avg_quiz_score, 1) if avg_quiz_score else None,
            'total_study_hours': total_study_hours,
            'last_activity': last_activity_time,
            'completed_lessons_count': completed_lessons,
            'recent_activities': recent_activities[:5],
            'student_display_name': display_name,
            'student_phone_number': phone_number,
            'unread_messages_count': Message.objects.filter(
                recipient=self.request.user,
                is_read=False
            ).count()
        })
        
        return context

    def _status_badge_class(self, status):
        if status == 'completed':
            return 'bg-success'
        if status == 'active':
            return 'bg-primary'
        if status == 'dropped':
            return 'bg-danger'
        if status == 'suspended':
            return 'bg-warning text-dark'
        return 'bg-secondary'


@login_required
@user_passes_test(lambda u: hasattr(u, 'instructor_profile'))
def send_message_to_student(request, student_id):
    """Send a message from instructor to student"""
    if request.method == 'POST':
        student = get_object_or_404(User, id=student_id)
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        
        if subject and content:
            Message.objects.create(
                sender=request.user,
                recipient=student,
                subject=subject,
                content=content
            )
            messages.success(request, f'Message sent to {student.get_full_name() or student.username} successfully!')
        else:
            messages.error(request, 'Please provide both subject and message content.')
    
    return redirect('users:instructor_student_detail', student_id=student_id)


@login_required
def instructor_course_detail(request, course_id):
    """Detailed view of a specific course for instructors"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user has permission to view this course
    try:
        instructor_profile = request.user.instructor_profile
        has_access = course.user_has_module_access(request.user)
        if instructor_profile.instructor_role != 'system_admin' and not has_access:
            messages.error(request, "You don't have permission to view this course.")
            return redirect('users:instructor_dashboard')
    except:
        messages.error(request, "You need to be a verified instructor to access this page.")
        return redirect('profile')
    
    # Get course analytics
    enrollments = course.enrollments.filter(status='active')
    total_students = enrollments.count()
    
    # Lesson progress
    lesson_progress_data = []
    for module in course.modules.all():
        for lesson in module.lessons.all():
            completed_count = LessonProgress.objects.filter(
                lesson=lesson,
                status='completed'
            ).count()
            
            completion_rate = (completed_count / max(total_students, 1)) * 100
            lesson_progress_data.append({
                'lesson': lesson,
                'completed_count': completed_count,
                'completion_rate': round(completion_rate, 1),
            })
    
    # Quiz performance
    quiz_data = []
    for module in course.modules.all():
        for lesson in module.lessons.all():
            if hasattr(lesson, 'quiz'):
                quiz = lesson.quiz
                attempts = quiz.attempts.all()
                if attempts.exists():
                    avg_score = attempts.aggregate(avg_score=Avg('score'))['avg_score']
                    pass_rate = attempts.filter(is_passed=True).count() / attempts.count() * 100
                    
                    quiz_data.append({
                        'quiz': quiz,
                        'total_attempts': attempts.count(),
                        'avg_score': round(avg_score, 1),
                        'pass_rate': round(pass_rate, 1),
                    })
    
    context = {
        'course': course,
        'total_students': total_students,
        'lesson_progress_data': lesson_progress_data,
        'quiz_data': quiz_data,
        'enrollments': enrollments[:10],  # Recent enrollments
    }
    
    return render(request, 'instructor/course_detail.html', context)


class InstructorTutorialView(InstructorRequiredMixin, TemplateView):
    """
    Comprehensive instructor tutorial page showing step-by-step course creation walkthrough
    """
    template_name = 'instructor/tutorial.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add any additional context data for the tutorial
        context['page_title'] = 'YITP LMS Instructor User Manual'
        context['tutorial_sections'] = [
            {
                'title': 'Scenario: Meet Beryl Omondi',
                'description': 'Understand the learner persona you are guiding through Youth Impact Training.',
                'steps': [
                    'Review Beryl’s goals inside the Students tab to personalize messaging.',
                    'Highlight outcomes that link back to her entrepreneurial ambitions.',
                    'Capture any blockers in Messages for follow up.'
                ]
            },
            {
                'title': 'Initial Setup & Course Creation',
                'description': 'Create modules and lessons that align with the approved curriculum.',
                'steps': [
                    'Navigate to My Modules → “Create Module”.',
                    'Add at least 3 learning outcomes per lesson before publishing.',
                    'Use estimated duration to keep pacing consistent across the cohort.'
                ]
            },
            {
                'title': 'Module Structure Planning',
                'description': 'Organize lessons so students always know what comes next.',
                'steps': [
                    'Drag lessons to reorder by difficulty or chronology.',
                    'Tag mandatory lessons to prevent students from skipping prerequisites.',
                    'Preview the module outline from the student view before publishing.'
                ]
            },
            {
                'title': 'Content Development',
                'description': 'Build rich lessons using the editor and reuse approved assets.',
                'steps': [
                    'Start with a hook; use the quote component or video embed.',
                    'Break content into sections with callouts for activities.',
                    'End each lesson with reflection prompts or a resource list.'
                ]
            },
            {
                'title': 'Multimedia Integration',
                'description': 'Keep learners engaged with video, audio, and downloadable resources.',
                'steps': [
                    'Upload files via Content Management so they stay versioned.',
                    'Provide transcripts for all videos to support accessibility.',
                    'Use galleries for before/after examples or case studies.'
                ]
            },
            {
                'title': 'Assessment Creation',
                'description': 'Measure competency with quizzes, assignments, or projects.',
                'steps': [
                    'Define pass criteria and number of attempts before publishing.',
                    'Mix question types—e.g., scenario-based MCQs plus reflections.',
                    'Attach rubrics so graders score consistently.'
                ]
            },
            {
                'title': 'Course Review & Publishing',
                'description': 'Verify every module is polished before making it live.',
                'steps': [
                    'Run the pre-launch checklist (assets, captions, accessibility).',
                    'Share the preview link with a peer instructor for QA.',
                    'Publish modules during off-peak hours to minimize impact.'
                ]
            },
            {
                'title': 'Student Management & Analytics',
                'description': 'Respond fast to student signals across tabs.',
                'steps': [
                    'Monitor lagging students from the Students tab each Monday.',
                    'Use Analytics to spot lessons with unusual drop-off.',
                    'Send nudges via Messages and log action items.'
                ]
            },
        ]
        context['unread_messages_count'] = Message.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()

        return context
