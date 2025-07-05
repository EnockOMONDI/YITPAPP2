"""
YITP Smart Redirect Middleware
Provides intelligent routing based on user authentication status and context
"""

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin


class SmartRedirectMiddleware(MiddlewareMixin):
    """
    Middleware that provides intelligent routing for YITP users
    """
    
    def process_request(self, request):
        """
        Process incoming requests and apply smart redirect logic
        """
        # Skip middleware for admin, API, and static files
        if (request.path.startswith('/admin/') or 
            request.path.startswith('/api/') or 
            request.path.startswith('/static/') or 
            request.path.startswith('/media/')):
            return None
        
        # Skip for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return None
        
        # Skip for POST requests (form submissions)
        if request.method == 'POST':
            return None
        
        # Apply smart redirects based on authentication status and path
        return self._apply_smart_redirects(request)
    
    def _apply_smart_redirects(self, request):
        """
        Apply intelligent redirect logic based on user status and requested path
        """
        user = request.user
        path = request.path
        
        # Redirect authenticated users away from registration/login pages
        if user.is_authenticated:
            if path in ['/registration/', '/registration2/', '/login/', '/signup/', '/register/']:
                # Check if user has course enrollments
                try:
                    from courses.models import Enrollment
                    has_enrollments = Enrollment.objects.filter(student=user).exists()
                    
                    if has_enrollments:
                        return redirect('courses:dashboard')
                    else:
                        return redirect('courses:course_list')
                except:
                    # Fallback if courses app is not available
                    return redirect('yitp:home')
        
        # Redirect unauthenticated users from LMS-specific pages to appropriate alternatives
        elif not user.is_authenticated:
            if path.startswith('/lms/'):
                # Redirect to login with next parameter
                return redirect(f'/login/?next={path}')
            
            # Redirect from dashboard/profile pages to home
            if path in ['/dashboard/', '/profile/']:
                return redirect('yitp:home')
        
        # No redirect needed
        return None


class CourseDiscoveryRedirectMiddleware(MiddlewareMixin):
    """
    Middleware that handles course discovery redirects
    """
    
    def process_request(self, request):
        """
        Handle course discovery page redirects based on user authentication
        """
        # Skip for non-GET requests
        if request.method != 'GET':
            return None
        
        path = request.path
        user = request.user
        
        # Handle course discovery redirects
        if path == '/web_courses_list/':
            if user.is_authenticated:
                # Redirect authenticated users to LMS course listing
                return redirect('courses:course_list')
        
        # Handle legacy registration redirects
        if path in ['/registration/', '/registration2/', '/join/']:
            return redirect('register')
        
        return None


class WelcomePageRedirectMiddleware(MiddlewareMixin):
    """
    Middleware that handles welcome page smart redirects
    """
    
    def process_request(self, request):
        """
        Handle welcome page redirects for returning users
        """
        # Skip for non-GET requests
        if request.method != 'GET':
            return None
        
        path = request.path
        user = request.user
        
        # Handle welcome page for returning users
        if path == '/welcome/' and user.is_authenticated:
            # Check if user just completed OTP verification
            just_completed_otp = request.session.get('just_completed_otp_verification', False)

            if just_completed_otp:
                # Clear the session flag and allow access to welcome page
                request.session.pop('just_completed_otp_verification', None)
                request.session.pop('otp_verification_timestamp', None)
                return None  # Continue to welcome page

            try:
                from progress.models import Enrollment
                from django.utils import timezone
                from datetime import timedelta

                # Check if user has been active recently (within last 7 days)
                recent_enrollments = Enrollment.objects.filter(
                    student=user,
                    enrollment_date__gte=timezone.now() - timedelta(days=7)
                )

                # If user has recent enrollments, redirect to dashboard
                if recent_enrollments.exists():
                    return redirect('courses:dashboard')

            except:
                # Fallback - continue to welcome page
                pass
        
        return None


class UnifiedNavigationMiddleware(MiddlewareMixin):
    """
    Middleware that adds unified navigation context to all requests
    """
    
    def process_request(self, request):
        """
        Add unified navigation context
        """
        # Add navigation context to request
        request.unified_nav_context = {
            'is_authenticated': request.user.is_authenticated,
            'user': request.user if request.user.is_authenticated else None,
            'current_path': request.path,
            'show_lms_nav': request.user.is_authenticated,
            'show_marketing_nav': not request.user.is_authenticated,
        }
        
        return None
