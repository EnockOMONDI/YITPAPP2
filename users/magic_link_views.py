"""
Magic Link Authentication Views for YITP
Handle magic link authentication and related functionality
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
import logging

from .magic_link_utils import (
    authenticate_user_with_magic_link,
    validate_magic_link_token,
    get_user_magic_tokens
)

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def magic_login_view(request, token):
    """
    Handle magic link authentication
    
    Args:
        request: Django request object
        token: Magic link token from URL
    
    Returns:
        HttpResponse: Redirect to appropriate page or error page
    """
    logger.info(f"Magic link authentication attempt with token: {token[:20]}...")
    
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        messages.info(request, "You are already logged in.")
        
        # Check if user is an instructor
        if hasattr(request.user, 'instructor_profile'):
            return redirect('users:instructor_dashboard')
        else:
            return redirect('yitp:home')
    
    # Attempt to authenticate with magic link
    success, message, user = authenticate_user_with_magic_link(request, token)
    
    if success:
        # Authentication successful
        messages.success(request, f"Welcome back, {user.first_name or user.username}! You've been automatically logged in.")
        
        # Determine redirect destination
        if hasattr(user, 'instructor_profile'):
            # Instructor user - redirect to instructor dashboard
            redirect_url = reverse('users:instructor_dashboard')
            messages.info(request, "Welcome to your instructor dashboard!")
        else:
            # Regular user - redirect to home
            redirect_url = reverse('yitp:home')
        
        logger.info(f"Magic link authentication successful for user {user.username}")
        return redirect(redirect_url)
    
    else:
        # Authentication failed
        logger.warning(f"Magic link authentication failed: {message}")
        
        # Render error page with appropriate message
        context = {
            'error_title': 'Magic Link Authentication Failed',
            'error_message': message,
            'error_details': [
                'The magic link may have expired (links are valid for 10 days)',
                'The magic link may have already been used',
                'The magic link may be invalid or corrupted',
            ],
            'suggested_actions': [
                'Try logging in with your username and password',
                'Request a new magic link if available',
                'Contact support if you continue to have issues',
            ],
            'login_url': reverse('login'),
            'support_email': getattr(settings, 'ADMIN_EMAIL', 'info@youthimpactglobal.com'),
        }
        
        return render(request, 'users/magic_link_error.html', context, status=400)

@login_required
@require_http_methods(["GET"])
def magic_link_status_view(request):
    """
    Show magic link status for the current user
    For debugging and user information purposes
    """
    user = request.user
    
    # Get user's magic link tokens
    tokens = get_user_magic_tokens(user)
    
    # Prepare token information
    token_info = []
    for token in tokens:
        token_info.append({
            'purpose': token.purpose,
            'created_at': token.created_at,
            'expires_at': token.expires_at,
            'is_used': token.is_used,
            'used_at': token.used_at,
            'is_expired': token.is_expired(),
            'is_valid': token.is_valid(),
        })
    
    context = {
        'user': user,
        'tokens': token_info,
        'total_tokens': len(token_info),
        'active_tokens': len([t for t in token_info if t['is_valid']]),
    }
    
    return render(request, 'users/magic_link_status.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def validate_magic_link_api(request):
    """
    API endpoint to validate a magic link token
    For AJAX validation or external integrations
    """
    token = request.POST.get('token') or request.GET.get('token')
    
    if not token:
        return JsonResponse({
            'valid': False,
            'error': 'No token provided'
        }, status=400)
    
    # Validate the token
    is_valid, user_or_error, magic_token = validate_magic_link_token(token)
    
    if is_valid:
        user = user_or_error
        return JsonResponse({
            'valid': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'token_purpose': magic_token.purpose,
            'expires_at': magic_token.expires_at.isoformat(),
        })
    else:
        return JsonResponse({
            'valid': False,
            'error': user_or_error
        }, status=400)

def magic_link_help_view(request):
    """
    Help page explaining magic links
    """
    context = {
        'page_title': 'Magic Link Help',
        'site_name': 'YITP Learning Management System',
        'support_email': getattr(settings, 'ADMIN_EMAIL', 'info@youthimpactglobal.com'),
    }
    
    return render(request, 'users/magic_link_help.html', context)
