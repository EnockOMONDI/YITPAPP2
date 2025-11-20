"""
YITP Smart Redirect Middleware
Provides intelligent routing based on user authentication status and context
"""

import logging

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SmartRedirectMiddleware(MiddlewareMixin):
    """
    Middleware that provides intelligent routing for YITP users
    """

    _AUTH_BLOCKLIST = {
        '/registration/', '/registration2/', '/login/', '/signup/', '/register/'
    }

    def process_request(self, request):
        """
        Process incoming requests and apply smart redirect logic
        """
        if (request.path.startswith('/admin/') or
                request.path.startswith('/api/') or
                request.path.startswith('/static/') or
                request.path.startswith('/media/')):
            return None

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return None

        if request.method == 'POST':
            return None

        return self._apply_smart_redirects(request)

    def _apply_smart_redirects(self, request):
        """
        Apply intelligent redirect logic based on user status and requested path
        """
        user = request.user
        path = request.path

        if user.is_authenticated:
            role_destination = self._get_role_destination(user)

            if path in self._AUTH_BLOCKLIST:
                try:
                    return redirect(role_destination)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error(
                        "Failed redirect for user %s to %s due to %s",
                        getattr(user, 'id', 'anonymous'),
                        role_destination,
                        exc,
                    )
                    return redirect('profile')

        else:
            if path.startswith('/lms/'):
                return redirect(f'/login/?next={path}')

            if path in ['/dashboard/', '/profile/']:
                return redirect('yitp:home')

        return None

    def _get_role_destination(self, user):
        """
        Determine the destination route based on the authenticated user's role
        """
        if getattr(user, 'is_superuser', False):
            return 'users:superuser_dashboard'

        instructor_profile = getattr(user, 'instructor_profile', None)
        if instructor_profile and getattr(instructor_profile, 'is_active', False):
            return 'users:instructor_profile'

        return 'profile'


class CourseDiscoveryRedirectMiddleware(MiddlewareMixin):
    """
    Middleware that handles course discovery redirects
    """

    def process_request(self, request):
        """
        Handle course discovery page redirects based on user authentication
        """
        if request.method != 'GET':
            return None

        path = request.path
        user = request.user

        if path == '/web_courses_list/' and user.is_authenticated:
            return redirect('courses:course_list')

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
        if request.method != 'GET':
            return None

        path = request.path
        user = request.user

        if path == '/welcome/' and user.is_authenticated:
            just_completed_otp = request.session.get('just_completed_otp_verification', False)

            if just_completed_otp:
                request.session.pop('just_completed_otp_verification', None)
                request.session.pop('otp_verification_timestamp', None)
                return None

            try:
                from progress.models import Enrollment
                from django.utils import timezone
                from datetime import timedelta

                recent_enrollments = Enrollment.objects.filter(
                    student=user,
                    enrollment_date__gte=timezone.now() - timedelta(days=7)
                )

                if recent_enrollments.exists():
                    if getattr(user, 'is_superuser', False):
                        return redirect('users:superuser_dashboard')
                    instructor_profile = getattr(user, 'instructor_profile', None)
                    if instructor_profile and getattr(instructor_profile, 'is_active', False):
                        return redirect('users:instructor_profile')
                    return redirect('profile')

            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Welcome redirect fallback triggered for user %s: %s", user.id, exc)

        return None


class UnifiedNavigationMiddleware(MiddlewareMixin):
    """
    Middleware that adds unified navigation context to all requests
    """

    def process_request(self, request):
        """
        Add unified navigation context
        """
        request.unified_nav_context = {
            'is_authenticated': request.user.is_authenticated,
            'user': request.user if request.user.is_authenticated else None,
            'current_path': request.path,
            'show_lms_nav': request.user.is_authenticated,
            'show_marketing_nav': not request.user.is_authenticated,
        }

        return None
