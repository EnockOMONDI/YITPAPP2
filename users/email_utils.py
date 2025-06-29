"""
Email utilities for YITP application
Handles OTP generation, email sending, and template management
"""
import random
import string
from datetime import datetime, timedelta
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_html_email(subject, html_content, recipient_list, from_email=None, plain_text_content=None):
    """
    Send HTML email with fallback to plain text
    """
    try:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        if plain_text_content is None:
            plain_text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_text_content,
            from_email=from_email,
            to=recipient_list
        )
        email.attach_alternative(html_content, "text/html")
        
        result = email.send()
        logger.info(f"Email sent successfully to {recipient_list}")
        return result
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
        return False

def send_otp_email(user, otp_code):
    """Send OTP verification email to user"""
    context = {
        'user': user,
        'otp_code': otp_code,
        'expiry_minutes': settings.OTP_EXPIRY_MINUTES,
        'site_name': 'Youth Impact Training Programme',
        'support_email': settings.ADMIN_EMAIL
    }
    
    html_content = render_to_string('emails/otp_verification.html', context)
    plain_content = render_to_string('emails/otp_verification.txt', context)
    
    subject = f"Your YITP Verification Code: {otp_code}"
    
    return send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user.email],
        plain_text_content=plain_content
    )

def send_welcome_email(user):
    """Send welcome email to newly registered user"""
    context = {
        'user': user,
        'site_name': 'Youth Impact Training Programme',
        'login_url': f"{settings.SITE_URL}/login/" if hasattr(settings, 'SITE_URL') else '/login/',
        'support_email': settings.ADMIN_EMAIL
    }
    
    html_content = render_to_string('emails/welcome.html', context)
    plain_content = render_to_string('emails/welcome.txt', context)
    
    subject = f"Welcome to YITP, {user.first_name or user.username}!"
    
    return send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user.email],
        plain_text_content=plain_content
    )

def send_login_notification(user, request):
    """Send login notification email"""
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Get user agent
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    
    context = {
        'user': user,
        'login_time': timezone.now(),
        'ip_address': ip,
        'user_agent': user_agent,
        'site_name': 'Youth Impact Training Programme',
        'support_email': settings.ADMIN_EMAIL
    }
    
    html_content = render_to_string('emails/login_notification.html', context)
    plain_content = render_to_string('emails/login_notification.txt', context)
    
    subject = "YITP Account Login Notification"
    
    return send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user.email],
        plain_text_content=plain_content
    )

def send_sponsorship_confirmation_email(sponsorship_request):
    """Send confirmation email when sponsorship request is submitted"""
    context = {
        'user': sponsorship_request.user,
        'sponsorship_request': sponsorship_request,
        'site_name': 'Youth Impact Training Programme',
        'support_email': settings.ADMIN_EMAIL
    }
    
    html_content = render_to_string('emails/sponsorship_confirmation.html', context)
    plain_content = render_to_string('emails/sponsorship_confirmation.txt', context)
    
    subject = "YITP Sponsorship Request Received - Confirmation"
    
    return send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[sponsorship_request.user.email],
        plain_text_content=plain_content
    )

def send_sponsorship_admin_notification(sponsorship_request):
    """Send notification to admin when new sponsorship request is submitted"""
    context = {
        'sponsorship_request': sponsorship_request,
        'user': sponsorship_request.user,
        'admin_url': f"{settings.SITE_URL}/admin/users/sponsorshiprequest/{sponsorship_request.id}/change/" if hasattr(settings, 'SITE_URL') else f"/admin/users/sponsorshiprequest/{sponsorship_request.id}/change/",
        'site_name': 'Youth Impact Training Programme'
    }
    
    html_content = render_to_string('emails/sponsorship_admin_notification.html', context)
    plain_content = render_to_string('emails/sponsorship_admin_notification.txt', context)
    
    subject = f"New YITP Sponsorship Request - {sponsorship_request.user.get_full_name() or sponsorship_request.user.username}"
    
    return send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[settings.ADMIN_EMAIL],
        plain_text_content=plain_content
    )

def send_sponsorship_status_update_email(sponsorship_request, old_status):
    """Send email when sponsorship request status is updated"""
    context = {
        'user': sponsorship_request.user,
        'sponsorship_request': sponsorship_request,
        'old_status': old_status,
        'new_status': sponsorship_request.status,
        'site_name': 'Youth Impact Training Programme',
        'support_email': settings.ADMIN_EMAIL
    }
    
    html_content = render_to_string('emails/sponsorship_status_update.html', context)
    plain_content = render_to_string('emails/sponsorship_status_update.txt', context)
    
    status_display = dict(sponsorship_request.STATUS_CHOICES).get(sponsorship_request.status, sponsorship_request.status)
    subject = f"YITP Sponsorship Request Update - {status_display}"
    
    return send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[sponsorship_request.user.email],
        plain_text_content=plain_content
    )

def send_sponsorship_status_admin_notification(sponsorship_request, old_status, updated_by):
    """Send notification to admin when sponsorship status is updated"""
    context = {
        'sponsorship_request': sponsorship_request,
        'user': sponsorship_request.user,
        'old_status': old_status,
        'new_status': sponsorship_request.status,
        'updated_by': updated_by,
        'admin_url': f"{settings.SITE_URL}/admin/users/sponsorshiprequest/{sponsorship_request.id}/change/" if hasattr(settings, 'SITE_URL') else f"/admin/users/sponsorshiprequest/{sponsorship_request.id}/change/",
        'site_name': 'Youth Impact Training Programme'
    }
    
    html_content = render_to_string('emails/sponsorship_status_admin_notification.html', context)
    plain_content = render_to_string('emails/sponsorship_status_admin_notification.txt', context)
    
    status_display = dict(sponsorship_request.STATUS_CHOICES).get(sponsorship_request.status, sponsorship_request.status)
    subject = f"YITP Sponsorship Status Updated - {sponsorship_request.user.get_full_name() or sponsorship_request.user.username} - {status_display}"
    
    return send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[settings.ADMIN_EMAIL],
        plain_text_content=plain_content
    )
