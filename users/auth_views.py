"""
Enhanced authentication views for YITP LMS with instructor-aware redirects
"""

from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from .models import InstructorProfile


class InstructorAwareLoginView(auth_views.LoginView):
    """
    Custom login view that redirects instructors to their dashboard
    """
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        """
        Redirect instructors to their dashboard, others to default page
        """
        user = self.request.user
        
        # Check if user has instructor profile
        try:
            instructor_profile = user.instructor_profile
            if instructor_profile.is_verified and instructor_profile.is_active:
                messages.success(
                    self.request, 
                    f"Welcome back, {user.get_full_name()}! You're logged in as {instructor_profile.get_instructor_role_display()}."
                )
                return reverse('users:instructor_dashboard')
        except:
            pass
        
        # Default redirect for non-instructors
        return super().get_success_url()


class InstructorProfileView(TemplateView):
    """
    Enhanced profile view that shows instructor-specific information
    """
    template_name = 'users/instructor_profile.html'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Check if user has instructor profile
        try:
            instructor_profile = user.instructor_profile
            context['instructor_profile'] = instructor_profile
            context['is_instructor'] = True
            context['specializations'] = instructor_profile.specializations.all()
            
            # Get instructor's courses
            if instructor_profile.instructor_role == 'system_admin':
                from courses.models import Course
                context['instructor_courses'] = Course.objects.all()[:5]
            else:
                context['instructor_courses'] = user.course_set.all()[:5]
            
            # Get recent messages
            from communication.models import Message
            context['recent_messages'] = Message.objects.filter(
                recipient=user
            ).order_by('-sent_at')[:3]
            
        except:
            context['is_instructor'] = False
            context['instructor_profile'] = None
        
        return context


@login_required
def instructor_onboarding_check(request):
    """
    Check if instructor needs onboarding and redirect appropriately
    """
    try:
        instructor_profile = request.user.instructor_profile
        
        # Check if instructor needs verification
        if instructor_profile.verification_status == 'pending':
            messages.info(
                request,
                "Your instructor profile is pending verification. You'll receive an email once approved."
            )
            return redirect('profile')
        
        # Check if instructor profile is incomplete
        if not instructor_profile.bio or not instructor_profile.qualifications:
            messages.warning(
                request,
                "Please complete your instructor profile to access all features."
            )
            return redirect('profile')
        
        # All good, redirect to dashboard
        return redirect('users:instructor_dashboard')
        
    except:
        messages.error(
            request,
            "You don't have an instructor profile. Please contact an administrator."
        )
        return redirect('profile')


class InstructorLogoutView(auth_views.LogoutView):
    """
    Custom logout view with instructor-specific messaging
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user was an instructor before logout
        if request.user.is_authenticated:
            try:
                instructor_profile = request.user.instructor_profile
                messages.success(
                    request,
                    f"You've been logged out successfully. Thank you for using YITP LMS, {instructor_profile.user.get_full_name()}!"
                )
            except:
                messages.success(request, "You've been logged out successfully.")
        
        return super().dispatch(request, *args, **kwargs)
