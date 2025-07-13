"""
Instructor-specific views for enhanced instructor experience
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta

from courses.models import Course, Module, Lesson
from assessments.models import Quiz
from progress.models import QuizAttempt, Enrollment, LessonProgress
from communication.models import Message, Notification
from .models import InstructorProfile


class InstructorRequiredMixin(UserPassesTestMixin):
    """Mixin to ensure user is a verified instructor"""
    
    def test_func(self):
        try:
            instructor_profile = self.request.user.instructor_profile
            return instructor_profile.is_verified and instructor_profile.is_active
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
    """Main instructor dashboard with overview and analytics"""
    template_name = 'instructor/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        instructor = self.request.user
        instructor_profile = instructor.instructor_profile
        
        # Get instructor's courses
        if instructor_profile.instructor_role == 'system_admin':
            instructor_courses = Course.objects.all()
        else:
            instructor_courses = Course.objects.filter(instructor=instructor)
        
        # Calculate statistics
        total_students = Enrollment.objects.filter(
            course__in=instructor_courses,
            status='active'
        ).count()
        
        total_courses = instructor_courses.count()
        published_courses = instructor_courses.filter(is_published=True).count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_enrollments = Enrollment.objects.filter(
            course__in=instructor_courses,
            enrollment_date__gte=thirty_days_ago
        ).count()
        
        # Quiz performance analytics
        quiz_attempts = QuizAttempt.objects.filter(
            quiz__lesson__module__course__in=instructor_courses,
            completed_at__gte=thirty_days_ago
        )
        
        avg_quiz_score = quiz_attempts.aggregate(
            avg_score=Avg('score')
        )['avg_score'] or 0
        
        # Recent messages
        recent_messages = Message.objects.filter(
            recipient=instructor,
            sent_at__gte=thirty_days_ago
        ).order_by('-sent_at')[:5]
        
        # Course performance data
        course_analytics = []
        for course in instructor_courses[:5]:  # Top 5 courses
            enrollments = course.enrollments.filter(status='active')
            completed_lessons = LessonProgress.objects.filter(
                enrollment__course=course,
                status='completed'
            ).count()
            
            total_lessons = course.total_lessons
            completion_rate = (completed_lessons / (total_lessons * enrollments.count() * 100)) if total_lessons and enrollments.count() else 0
            
            course_analytics.append({
                'course': course,
                'enrollments': enrollments.count(),
                'completion_rate': round(completion_rate, 1),
                'total_lessons': total_lessons,
            })
        
        context.update({
            'instructor_profile': instructor_profile,
            'total_students': total_students,
            'total_courses': total_courses,
            'published_courses': published_courses,
            'recent_enrollments': recent_enrollments,
            'avg_quiz_score': round(avg_quiz_score, 1),
            'recent_messages': recent_messages,
            'course_analytics': course_analytics,
            'instructor_courses': instructor_courses[:10],  # Recent courses
        })
        
        return context


class InstructorCoursesView(LoginRequiredMixin, InstructorRequiredMixin, ListView):
    """List view of instructor's courses with management options"""
    template_name = 'instructor/courses.html'
    context_object_name = 'courses'
    paginate_by = 12
    
    def get_queryset(self):
        instructor = self.request.user
        instructor_profile = instructor.instructor_profile
        
        if instructor_profile.instructor_role == 'system_admin':
            queryset = Course.objects.all()
        else:
            queryset = Course.objects.filter(instructor=instructor)
        
        # Filter by status if requested
        status = self.request.GET.get('status')
        if status == 'published':
            queryset = queryset.filter(is_published=True)
        elif status == 'draft':
            queryset = queryset.filter(is_published=False)
        elif status == 'featured':
            queryset = queryset.filter(is_featured=True)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
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


@login_required
def instructor_course_detail(request, course_id):
    """Detailed view of a specific course for instructors"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if user has permission to view this course
    try:
        instructor_profile = request.user.instructor_profile
        if instructor_profile.instructor_role != 'system_admin' and course.instructor != request.user:
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
            'Scenario Introduction: Meet Beryl Omondi',
            'Initial Setup & Course Creation',
            'Module Structure Planning',
            'Content Development',
            'Multimedia Integration',
            'Assessment Creation',
            'Course Review & Publishing',
            'Student Management & Analytics'
        ]

        return context
