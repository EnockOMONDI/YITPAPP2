"""
Trial Management Views for YITP
Handles trial enrollment, status checking, and conversion workflows
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging

from .models import Course
from .enrollment_service import EnrollmentService
from .trial_service import TrialAccessService
from progress.models import Enrollment

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def start_trial(request, course_slug):
    """
    Start trial enrollment for a course
    """
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    
    if request.method == 'GET':
        # Show trial enrollment page
        context = {
            'course': course,
            'trial_boundaries': TrialAccessService.DEFAULT_TRIAL_BOUNDARIES,
            'user_trial_status': TrialAccessService.get_user_trial_status(request.user)
        }
        return render(request, 'lms/trial/start_trial.html', context)
    
    elif request.method == 'POST':
        # Process trial enrollment
        try:
            result = EnrollmentService.enroll_user_in_trial(request.user, course)
            
            if result['success']:
                messages.success(
                    request, 
                    f"Trial started successfully! You now have access to the first 2 lessons of '{course.title}'."
                )
                logger.info(f"Trial enrollment successful: {request.user.email} -> {course.title}")
                
                # Redirect to first lesson
                first_lesson = course.get_ordered_lessons()[0] if course.get_ordered_lessons() else None
                if first_lesson:
                    return redirect('lms:lesson_detail', lesson_id=first_lesson.id)
                else:
                    return redirect('courses:course_detail', slug=course.slug)
            else:
                messages.error(request, result['message'])
                logger.warning(f"Trial enrollment failed: {request.user.email} -> {course.title}: {result['message']}")
                
        except Exception as e:
            messages.error(request, "An error occurred while starting your trial. Please try again.")
            logger.error(f"Trial enrollment error: {request.user.email} -> {course.title}: {str(e)}")
        
        return redirect('courses:course_detail', slug=course.slug)


@login_required
def trial_status(request, course_slug):
    """
    Get trial status for a course
    """
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    
    trial_status = TrialAccessService.get_user_trial_status(request.user)
    trial_progress = TrialAccessService.get_trial_progress_summary(request.user, course)
    upgrade_prompt = TrialAccessService.should_show_upgrade_prompt(request.user, course)
    
    context = {
        'course': course,
        'trial_status': trial_status,
        'trial_progress': trial_progress,
        'upgrade_prompt': upgrade_prompt
    }
    
    return render(request, 'lms/trial/trial_status.html', context)


@login_required
def trial_status_api(request, course_slug):
    """
    API endpoint for trial status (AJAX)
    """
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    
    trial_status = TrialAccessService.get_user_trial_status(request.user)
    trial_progress = TrialAccessService.get_trial_progress_summary(request.user, course)
    upgrade_prompt = TrialAccessService.should_show_upgrade_prompt(request.user, course)
    
    return JsonResponse({
        'trial_status': trial_status,
        'trial_progress': trial_progress,
        'upgrade_prompt': upgrade_prompt,
        'course_id': course.id,
        'course_title': course.title
    })


@login_required
@require_http_methods(["POST"])
def convert_trial_to_paid(request, course_slug):
    """
    Convert trial enrollment to paid enrollment after payment confirmation
    """
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    
    try:
        # Get trial enrollment
        trial_enrollment = TrialAccessService.get_trial_enrollment(request.user, course)
        if not trial_enrollment:
            messages.error(request, "No trial enrollment found for this course.")
            return redirect('courses:course_detail', slug=course.slug)
        
        # Check if user has payment access
        if not request.user.profile.has_any_payment_access:
            messages.error(request, "Payment verification required before converting trial to full access.")
            return redirect('courses:course_detail', slug=course.slug)
        
        # Convert trial to paid
        trial_enrollment.convert_trial_to_paid()
        
        messages.success(
            request, 
            f"Congratulations! Your trial has been converted to full access for '{course.title}'. "
            f"You now have access to all course content."
        )
        logger.info(f"Trial converted to paid: {request.user.email} -> {course.title}")
        
        return redirect('courses:course_detail', slug=course.slug)
        
    except Exception as e:
        messages.error(request, "An error occurred while converting your trial. Please contact support.")
        logger.error(f"Trial conversion error: {request.user.email} -> {course.title}: {str(e)}")
        return redirect('courses:course_detail', slug=course.slug)


@login_required
def check_lesson_access(request, lesson_id):
    """
    Check if user can access a specific lesson (considering trial boundaries)
    """
    from courses.models import Lesson
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    access_result = TrialAccessService.can_access_lesson(request.user, lesson)
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'can_access': access_result['can_access'],
            'reason': access_result['reason'],
            'is_trial_user': access_result['is_trial_user'],
            'lesson_position': access_result['lesson_position'],
            'lesson_title': lesson.title
        })
    
    # For non-AJAX requests, redirect with message
    if not access_result['can_access']:
        messages.warning(request, access_result['reason'])
        return redirect('courses:course_detail', slug=lesson.module.course.slug)
    
    return redirect('lms:lesson_detail', lesson_id=lesson_id)


@login_required
def check_quiz_access(request, quiz_id):
    """
    Check if user can access a specific quiz (considering trial boundaries)
    """
    from assessments.models import Quiz
    
    quiz = get_object_or_404(Quiz, id=quiz_id)
    access_result = TrialAccessService.can_access_quiz(request.user, quiz)
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'can_access': access_result['can_access'],
            'reason': access_result['reason'],
            'is_trial_user': access_result['is_trial_user'],
            'associated_lesson': access_result['associated_lesson'].title if access_result['associated_lesson'] else None,
            'quiz_title': quiz.title
        })
    
    # For non-AJAX requests, redirect with message
    if not access_result['can_access']:
        messages.warning(request, access_result['reason'])
        return redirect('courses:course_detail', slug=quiz.course.slug)
    
    return redirect('lms:quiz_detail', quiz_id=quiz_id)


@method_decorator(login_required, name='dispatch')
class TrialDashboardView(View):
    """
    Trial dashboard showing user's trial progress and options
    """
    
    def get(self, request):
        trial_status = TrialAccessService.get_user_trial_status(request.user)
        
        if not trial_status['has_trial']:
            messages.info(request, "You don't have any active trials.")
            return redirect('courses:course_list')
        
        trial_course = trial_status['trial_course']
        trial_progress = TrialAccessService.get_trial_progress_summary(request.user, trial_course)
        upgrade_prompt = TrialAccessService.should_show_upgrade_prompt(request.user, trial_course)
        
        # Get accessible content
        trial_enrollment = TrialAccessService.get_trial_enrollment(request.user, trial_course)
        accessible_lessons = trial_enrollment.get_trial_accessible_lessons() if trial_enrollment else []
        
        context = {
            'trial_status': trial_status,
            'trial_course': trial_course,
            'trial_progress': trial_progress,
            'upgrade_prompt': upgrade_prompt,
            'accessible_lessons': accessible_lessons,
            'trial_enrollment': trial_enrollment
        }
        
        return render(request, 'lms/trial/trial_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def track_trial_access(request):
    """
    Track trial user's access to content for analytics
    """
    try:
        data = json.loads(request.body)
        content_type = data.get('content_type')  # 'lesson' or 'quiz'
        content_id = data.get('content_id')
        
        if content_type and content_id:
            TrialAccessService.track_trial_access(request.user, content_type, content_id)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Missing required parameters'})
            
    except Exception as e:
        logger.error(f"Error tracking trial access: {str(e)}")
        return JsonResponse({'success': False, 'error': 'Internal error'})


@login_required
def trial_completion_summary(request, course_slug):
    """
    Show trial completion summary and upgrade options
    """
    course = get_object_or_404(Course, slug=course_slug, is_published=True)
    
    trial_progress = TrialAccessService.get_trial_progress_summary(request.user, course)
    
    if not trial_progress['is_trial_user']:
        messages.info(request, "This page is only available for trial users.")
        return redirect('courses:course_detail', slug=course.slug)
    
    context = {
        'course': course,
        'trial_progress': trial_progress,
        'payment_methods': [
            {'id': 'paypal', 'name': 'PayPal', 'icon': 'fab fa-paypal'},
            {'id': 'mpesa', 'name': 'M-Pesa', 'icon': 'fas fa-mobile-alt'},
            {'id': 'installment', 'name': '2-Installment Plan', 'icon': 'fas fa-calendar-alt'}
        ]
    }
    
    return render(request, 'lms/trial/trial_completion_summary.html', context)


# URL patterns for trial views (to be added to courses/urls.py)
"""
from django.urls import path
from . import trial_views

trial_urlpatterns = [
    path('trial/start/<slug:course_slug>/', trial_views.start_trial, name='start_trial'),
    path('trial/status/<slug:course_slug>/', trial_views.trial_status, name='trial_status'),
    path('trial/status-api/<slug:course_slug>/', trial_views.trial_status_api, name='trial_status_api'),
    path('trial/convert/<slug:course_slug>/', trial_views.convert_trial_to_paid, name='convert_trial_to_paid'),
    path('trial/lesson-access/<int:lesson_id>/', trial_views.check_lesson_access, name='check_lesson_access'),
    path('trial/quiz-access/<int:quiz_id>/', trial_views.check_quiz_access, name='check_quiz_access'),
    path('trial/dashboard/', trial_views.TrialDashboardView.as_view(), name='trial_dashboard'),
    path('trial/track-access/', trial_views.track_trial_access, name='track_trial_access'),
    path('trial/completion/<slug:course_slug>/', trial_views.trial_completion_summary, name='trial_completion_summary'),
]
"""
