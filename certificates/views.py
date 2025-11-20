from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404, FileResponse
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
import os
import mimetypes

from progress.models import Certificate
from courses.models import Lesson
from .certificate_service import CertificateService


class CertificateVerificationView(TemplateView):
    """
    Public certificate verification view (no login required)
    Allows anyone to verify certificate authenticity using verification code
    """
    template_name = 'certificates/verify.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        verification_code = kwargs.get('verification_code')
        
        # Verify certificate using CertificateService
        verification_result = CertificateService.verify_certificate(verification_code)
        
        context.update({
            'verification_code': verification_code,
            'verification_result': verification_result,
            'certificate': verification_result.get('certificate'),
            'is_valid': verification_result.get('valid', False),
            'message': verification_result.get('message', ''),
        })
        
        # Add additional certificate details if valid
        if verification_result.get('valid') and verification_result.get('certificate'):
            certificate = verification_result['certificate']
            context.update({
                'student_name': f"{certificate.enrollment.student.first_name} {certificate.enrollment.student.last_name}".strip() or certificate.enrollment.student.username,
                'course_title': certificate.enrollment.course.title,
                'completion_date': certificate.enrollment.completion_date or certificate.issued_date,
                'final_score': certificate.final_score,
                'certificate_id': certificate.certificate_id,
                'verification_url': f"{settings.SITE_URL}/certificates/verify/{verification_code}/",
            })
        
        return context


class CertificateDownloadView(LoginRequiredMixin, TemplateView):
    """
    Authenticated certificate download view
    Allows users to download their own certificates
    """
    
    def get(self, request, *args, **kwargs):
        verification_code = kwargs.get('verification_code')
        
        # Verify certificate exists and belongs to user
        try:
            certificate = Certificate.objects.get(verification_code=verification_code)
            
            # Check if user owns this certificate or is admin
            if certificate.enrollment.student != request.user and not request.user.is_staff:
                messages.error(request, "You don't have permission to download this certificate.")
                return redirect('certificates:my_certificates')
            
            # Try to serve existing certificate file stored in certificate_data (file_path)
            file_path = None
            if certificate.certificate_data:
                file_path = certificate.certificate_data.get('file_path')

            if file_path and os.path.exists(file_path):
                try:
                    return FileResponse(
                        open(file_path, 'rb'),
                        as_attachment=True,
                        filename=f"certificate_{certificate.certificate_id}.pdf"
                    )
                except Exception:
                    pass
            
            # Generate certificate on-the-fly if no file exists
            generation_result = CertificateService.generate_certificate(certificate.enrollment)
            
            if generation_result.get('success'):
                messages.success(request, "Certificate generated successfully. Download is now available.")
                new_path = generation_result.get('file_path')
                if new_path and os.path.exists(new_path):
                    return FileResponse(
                        open(new_path, 'rb'),
                        as_attachment=True,
                        filename=f"certificate_{certificate.certificate_id}.pdf"
                    )
                return redirect('certificates:verify', verification_code=verification_code)
            else:
                messages.error(request, f"Error generating certificate: {generation_result.get('message', 'Unknown error')}")
                return redirect('certificates:my_certificates')
                
        except Certificate.DoesNotExist:
            messages.error(request, "Certificate not found.")
            return redirect('certificates:my_certificates')


class MyCertificatesView(LoginRequiredMixin, ListView):
    """
    User's certificate list view
    Shows all certificates earned by the authenticated user
    """
    template_name = 'certificates/my_certificates.html'
    context_object_name = 'certificates'
    
    def get_queryset(self):
        return CertificateService.get_user_certificates(self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        certificates = context['certificates']
        
        # Calculate achievement statistics
        total_certificates = certificates.count()
        total_courses_completed = certificates.values('enrollment__course').distinct().count()
        
        # Calculate average score
        scores = [cert.final_score for cert in certificates if cert.final_score]
        average_score = sum(scores) / len(scores) if scores else 0
        
        context.update({
            'total_certificates': total_certificates,
            'total_courses_completed': total_courses_completed,
            'average_score': round(average_score, 1),
            'user_full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
        })
        
        return context


class CertificateDetailView(LoginRequiredMixin, DetailView):
    """
    Individual certificate detail view
    Shows comprehensive certificate information and achievements
    """
    template_name = 'certificates/certificate_detail.html'
    context_object_name = 'certificate'
    
    def get_object(self):
        verification_code = self.kwargs.get('verification_code')
        certificate = get_object_or_404(Certificate, verification_code=verification_code)
        
        # Check if user owns this certificate or is admin
        if certificate.enrollment.student != self.request.user and not self.request.user.is_staff:
            raise Http404("Certificate not found.")
        
        return certificate
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        certificate = context['certificate']
        enrollment = certificate.enrollment
        course = enrollment.course
        
        # Get course completion details
        from progress.models import LessonProgress, QuizAttempt
        
        lesson_progress = LessonProgress.objects.filter(
            enrollment=enrollment,
            status='completed'
        ).select_related('lesson')
        
        quiz_attempts = QuizAttempt.objects.filter(
            enrollment=enrollment,
            is_passed=True
        ).select_related('quiz')
        
        # Calculate achievements using Lesson objects (course has modules)
        published_lessons = Lesson.objects.filter(module__course=course, is_published=True)
        total_lessons = published_lessons.count()
        completed_lessons = lesson_progress.count()
        total_quizzes = sum(lesson.quizzes.filter(is_published=True).count() for lesson in published_lessons)
        passed_quizzes = quiz_attempts.count()
        
        # Get skills from course (if available)
        skills_acquired = []
        if hasattr(course, 'skills') and course.skills:
            skills_acquired = course.skills.split(',') if isinstance(course.skills, str) else []
        
        context.update({
            'student_name': f"{enrollment.student.first_name} {enrollment.student.last_name}".strip() or enrollment.student.username,
            'course_title': course.title,
            'completion_date': enrollment.completion_date or certificate.issued_date,
            'final_score': certificate.final_score,
            'certificate_id': certificate.certificate_id,
            'verification_code': certificate.verification_code,
            'verification_url': f"{settings.SITE_URL}/certificates/verify/{certificate.verification_code}/",
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'total_quizzes': total_quizzes,
            'passed_quizzes': passed_quizzes,
            'completion_rate': round((completed_lessons / total_lessons * 100) if total_lessons > 0 else 0, 1),
            'quiz_success_rate': round((passed_quizzes / total_quizzes * 100) if total_quizzes > 0 else 0, 1),
            'skills_acquired': skills_acquired,
            'lesson_progress': lesson_progress,
            'quiz_attempts': quiz_attempts,
        })
        
        return context
