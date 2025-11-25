"""
Email utilities for YITP application
Handles OTP generation, email sending, and template management
"""
import os
import sys
import random
import string
import re
import json
from datetime import datetime, timedelta
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
import logging

# Import Mailtrap service for email sending
from users.mailtrap_service import mailtrap_service

#updates#updates#updates
logger = logging.getLogger(__name__)

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))


def generate_secure_temporary_password(length=12):
    """
    Generate a secure temporary password for instructor accounts

    Args:
        length: Password length (minimum 12 characters)

    Returns:
        str: Secure temporary password meeting complexity requirements
    """
    if length < 12:
        length = 12

    # Define character sets
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    special_chars = "!@#$%^&*"

    # Ensure at least one character from each set
    password = [
        random.choice(uppercase),
        random.choice(lowercase),
        random.choice(digits),
        random.choice(special_chars)
    ]

    # Fill remaining length with random characters from all sets
    all_chars = uppercase + lowercase + digits + special_chars
    for _ in range(length - 4):
        password.append(random.choice(all_chars))

    # Shuffle the password list to randomize positions
    random.shuffle(password)

    return ''.join(password)


def validate_password_complexity(password):
    """
    Validate password meets YITP security requirements

    Args:
        password: Password string to validate

    Returns:
        tuple: (is_valid: bool, errors: list)
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")

    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")

    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")

    # Check for common weak patterns
    common_patterns = ['123456', 'password', 'qwerty', 'abc123']
    if any(pattern in password.lower() for pattern in common_patterns):
        errors.append("Password contains common weak patterns")

    return len(errors) == 0, errors


def log_instructor_account_creation(user, instructor_profile, created_by_admin, email_sent=False):
    """
    Log instructor account creation for audit purposes

    Args:
        user: User instance
        instructor_profile: InstructorProfile instance
        created_by_admin: Admin user who created the account
        email_sent: Whether welcome email was sent successfully
    """
    try:
        audit_data = {
            'action': 'instructor_account_created',
            'instructor_username': user.username,
            'instructor_email': user.email,
            'instructor_role': instructor_profile.instructor_role,
            'verification_status': instructor_profile.verification_status,
            'created_by': created_by_admin.username if created_by_admin else 'system',
            'created_by_email': created_by_admin.email if created_by_admin else 'system',
            'email_notification_sent': email_sent,
            'timestamp': timezone.now().isoformat(),
            'permissions_granted': instructor_profile.get_permissions_summary()
        }

        # Log to Django logger
        logger.info(f"INSTRUCTOR_AUDIT: {json.dumps(audit_data, indent=2)}")

        # Also log to a separate audit file if configured
        audit_logger = logging.getLogger('instructor_audit')
        audit_logger.info(json.dumps(audit_data))

    except Exception as e:
        logger.error(f"Failed to log instructor account creation audit: {str(e)}")


def create_instructor_with_temporary_password(username, email, first_name, last_name, instructor_role, created_by_admin):
    """
    Create instructor account with secure temporary password and send welcome email

    Args:
        username: Username for the new instructor
        email: Email address for the new instructor
        first_name: First name
        last_name: Last name
        instructor_role: Role from InstructorProfile.INSTRUCTOR_ROLES
        created_by_admin: Admin user creating the account

    Returns:
        dict: {
            'success': bool,
            'user': User instance or None,
            'instructor_profile': InstructorProfile instance or None,
            'temporary_password': str or None,
            'email_sent': bool,
            'message': str
        }
    """
    try:
        from django.contrib.auth.models import User
        from .models import InstructorProfile

        # Generate secure temporary password
        temporary_password = generate_secure_temporary_password()

        # Validate password (should always pass, but good to check)
        is_valid, errors = validate_password_complexity(temporary_password)
        if not is_valid:
            logger.error(f"Generated temporary password failed validation: {errors}")
            # Generate a new one
            temporary_password = generate_secure_temporary_password(16)

        # Create user account
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=temporary_password
        )

        # Create instructor profile (this will trigger the signal)
        instructor_profile = InstructorProfile.objects.create(
            user=user,
            instructor_role=instructor_role,
            verification_status='pending'  # Will be auto-verified for system_admin
        )

        # Send welcome email
        email_sent = send_instructor_welcome_email(
            user=user,
            instructor_profile=instructor_profile,
            temporary_password=temporary_password,
            created_by_admin=created_by_admin
        )

        # Log the account creation
        log_instructor_account_creation(
            user=user,
            instructor_profile=instructor_profile,
            created_by_admin=created_by_admin,
            email_sent=email_sent
        )

        return {
            'success': True,
            'user': user,
            'instructor_profile': instructor_profile,
            'temporary_password': temporary_password,
            'email_sent': email_sent,
            'message': f'Instructor account created successfully for {email}'
        }

    except Exception as e:
        logger.error(f"Failed to create instructor account: {str(e)}")
        return {
            'success': False,
            'user': None,
            'instructor_profile': None,
            'temporary_password': None,
            'email_sent': False,
            'message': f'Failed to create instructor account: {str(e)}'
        }

def test_email_configuration():
    """
    Test email configuration and connectivity
    Returns detailed information about email setup
    """
    import smtplib
    import ssl

    try:
        logger.info("🔍 Testing email configuration...")

        # Check settings
        config_info = {
            'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'Not set'),
            'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'Not set'),
            'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', 'Not set'),
            'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'Not set'),
            'EMAIL_HOST_PASSWORD': '***' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'Not set',
            'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set'),
        }

        logger.info(f"Email configuration: {config_info}")

        # Test SMTP connection
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls(context=context)
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.quit()

        logger.info("✅ Email configuration test successful")
        return {
            'success': True,
            'message': 'Email configuration is working correctly',
            'config': config_info
        }

    except Exception as e:
        logger.error(f"❌ Email configuration test failed: {str(e)}")
        return {
            'success': False,
            'message': f'Email configuration test failed: {str(e)}',
            'config': config_info if 'config_info' in locals() else {}
        }

def send_html_email_direct(subject, html_content, recipient_list, from_email=None, plain_text_content=None):
    """
    Send HTML email using Mailtrap API
    Replaces the old Gmail SMTP direct method
    """
    logger.info(f"📧 Sending email via Mailtrap API to {recipient_list}")
    logger.info(f"Subject: {subject}")

    # Use Mailtrap service for email sending
    return mailtrap_service.send_email(
        subject=subject,
        html_content=html_content,
        recipient_list=recipient_list,
        from_email=from_email,
        plain_text_content=plain_text_content
    )

def send_html_email(subject, html_content, recipient_list, from_email=None, plain_text_content=None):
    """
    Send HTML email using Mailtrap API
    Maintains compatibility with existing function signature
    """
    # Check if we're in test environment - use Django backend for tests
    if hasattr(settings, 'EMAIL_BACKEND') and 'locmem' in settings.EMAIL_BACKEND:
        logger.info("Test environment detected, using Django email backend directly")

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

            if result:
                logger.info(f"✅ Test email sent via Django backend to {recipient_list}")
                return True
            else:
                logger.warning(f"⚠️ Django backend returned 0 for {recipient_list}")
                return False

        except Exception as e:
            logger.error(f"❌ Django backend failed for {recipient_list}: {str(e)}")
            return False

    elif 'test' in sys.argv or os.environ.get('DJANGO_TESTING'):
        logger.info("Test environment detected via command line or environment")
        return True  # Skip actual sending in test environment

    else:
        # Production: Use Mailtrap API
        logger.info(f"📧 Sending email via Mailtrap API to {recipient_list}")
        return mailtrap_service.send_email(
            subject=subject,
            html_content=html_content,
            recipient_list=recipient_list,
            from_email=from_email,
            plain_text_content=plain_text_content
        )

def test_email_configuration_simple():
    """
    Simple email configuration test by sending a test email
    Returns True if successful, False otherwise
    """
    try:
        test_subject = "YITP Email Configuration Test"
        test_content = """
        <h2>Email Configuration Test</h2>
        <p>This is a test email to verify YITP email configuration is working correctly.</p>
        <p>If you receive this email, the configuration is successful!</p>
        """

        result = send_html_email(
            subject=test_subject,
            html_content=test_content,
            recipient_list=[settings.ADMIN_EMAIL]
        )

        logger.info(f"Email configuration test result: {result}")
        return result

    except Exception as e:
        logger.error(f"Email configuration test failed: {str(e)}")
        return False

def send_otp_email(user, otp_code):
    """Send OTP verification email to user with enhanced verification link"""
    logger.info(f"Preparing to send OTP email to {user.email}")

    # Create verification URL with user ID and auto-fill capability
    base_url = getattr(settings, 'SITE_URL', 'https://www.youthimpactglobal.com')
    verification_url = f"{base_url}/verify-otp/?user_id={user.id}&code={otp_code}"

    context = {
        'user': user,
        'otp_code': otp_code,
        'verification_url': verification_url,
        'expiry_minutes': settings.OTP_EXPIRY_MINUTES,
        'site_name': 'Youth Impact Training Programme',
        'support_email': settings.ADMIN_EMAIL
    }

    html_content = render_to_string('emails/otp_verification.html', context)
    plain_content = render_to_string('emails/otp_verification.txt', context)

    subject = f"Your YITP Verification Code: {otp_code}"

    logger.info(f"Sending OTP email with subject: {subject}")

    result = send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user.email],
        plain_text_content=plain_content
    )

    if result:
        logger.info(f"✅ OTP email sent successfully to {user.email}")
    else:
        logger.error(f"❌ Failed to send OTP email to {user.email}")

    return result

def send_verification_reminder_email(user, otp_code, reminder_count):
    """Send verification reminder email to unverified user"""
    logger.info(f"Preparing to send verification reminder #{reminder_count} to {user.email}")

    # Create verification URL with user ID and auto-fill capability
    base_url = getattr(settings, 'SITE_URL', 'https://www.youthimpactglobal.com')
    verification_url = f"{base_url}/verify-otp/?user_id={user.id}&code={otp_code}"

    # Calculate days remaining (7 days total from registration)
    from datetime import timedelta
    from django.utils import timezone

    registration_date = user.date_joined
    deadline = registration_date + timedelta(days=7)
    days_remaining = (deadline - timezone.now()).days
    if days_remaining < 0:
        days_remaining = 0

    context = {
        'user': user,
        'otp_code': otp_code,
        'verification_url': verification_url,
        'reminder_count': reminder_count,
        'days_remaining': days_remaining,
        'expiry_minutes': settings.OTP_EXPIRY_MINUTES,
        'site_name': 'Youth Impact Training Programme',
        'support_email': settings.ADMIN_EMAIL
    }

    html_content = render_to_string('emails/verification_reminder.html', context)
    plain_content = render_to_string('emails/verification_reminder.txt', context)

    subject = f"YITP Account Verification Reminder - Complete Your Registration"

    logger.info(f"Sending verification reminder email with subject: {subject}")

    result = send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user.email],
        plain_text_content=plain_content
    )

    if result:
        logger.info(f"✅ Verification reminder email sent successfully to {user.email}")
    else:
        logger.error(f"❌ Failed to send verification reminder email to {user.email}")

    return result

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
    """Send login notification email to user and admin notification for instructors"""
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    # Get user agent
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')

    # Send user notification
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

    user_notification_result = send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user.email],
        plain_text_content=plain_content
    )

    # Send admin notification for instructor logins
    admin_notification_result = False
    try:
        if hasattr(user, 'instructor_profile'):
            admin_notification_result = send_instructor_login_notification(
                user=user,
                login_timestamp=timezone.now(),
                ip_address=ip,
                user_agent=user_agent
            )
    except Exception as e:
        logger.error(f"Failed to send instructor login admin notification: {str(e)}")

    return user_notification_result

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


def send_enrollment_confirmation_email(user, course, enrollment, payment_context=None):
    """Send enrollment confirmation email to user with payment context"""
    logger.info(f"Preparing to send enrollment confirmation email to {user.email} for course {course.title}")

    context = {
        'user': user,
        'course': course,
        'enrollment': enrollment,
        'enrollment_date': enrollment.enrollment_date,
        'course_url': f"{settings.SITE_URL}/lms/courses/{course.slug}/" if hasattr(settings, 'SITE_URL') else f"/lms/courses/{course.slug}/",
        'base_url': getattr(settings, 'SITE_URL', 'https://www.youthimpactglobal.com'),
        'support_email': settings.ADMIN_EMAIL,
        'site_name': 'Youth Impact Training Programme',
        # Payment context
        'payment_status': payment_context.get('payment_status', 'pending') if payment_context else 'pending',
        'is_installment': payment_context.get('is_installment', False) if payment_context else False,
        'installment_sequence': payment_context.get('installment_sequence', 1) if payment_context else 1,
    }

    html_content = render_to_string('emails/enrollment_confirmation.html', context)
    plain_content = render_to_string('emails/enrollment_confirmation.txt', context)

    subject = f"Course Enrollment Confirmed: {course.title} - YITP"

    logger.info(f"Sending enrollment confirmation email with subject: {subject}")

    result = send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user.email],
        plain_text_content=plain_content
    )

    if result:
        logger.info(f"✅ Enrollment confirmation email sent successfully to {user.email}")
    else:
        logger.error(f"❌ Failed to send enrollment confirmation email to {user.email}")

    return result


def send_enrollment_admin_notification(user, course, enrollment, payment_context=None):
    """Send enrollment notification email to admin with payment context"""
    logger.info(f"Preparing to send enrollment admin notification for {user.email} enrolling in {course.title}")

    # Calculate enrollment statistics
    total_enrolled = course.enrolled_students_count
    remaining_spots = None
    if course.enrollment_limit:
        remaining_spots = course.enrollment_limit - total_enrolled

    context = {
        'user': user,
        'course': course,
        'enrollment_date': enrollment.enrollment_date,
        'total_enrolled': total_enrolled,
        'remaining_spots': remaining_spots,
        'admin_url': f"{settings.SITE_URL}/admin/progress/enrollment/{enrollment.id}/change/" if hasattr(settings, 'SITE_URL') else f"/admin/progress/enrollment/{enrollment.id}/change/",
        'site_name': 'Youth Impact Training Programme',
        # Payment context
        'payment_status': payment_context.get('payment_status', 'pending') if payment_context else 'pending',
        'is_installment': payment_context.get('is_installment', False) if payment_context else False,
        'installment_sequence': payment_context.get('installment_sequence', 1) if payment_context else 1,
    }

    html_content = render_to_string('emails/enrollment_admin_notification.html', context)
    plain_content = render_to_string('emails/enrollment_admin_notification.txt', context)

    subject = f"New Enrollment: {user.get_full_name()} → {course.title} - YITP"

    logger.info(f"Sending enrollment admin notification with subject: {subject}")

    result = send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[settings.ADMIN_EMAIL],
        plain_text_content=plain_content
    )

    if result:
        logger.info(f"✅ Enrollment admin notification sent successfully")
    else:
        logger.error(f"❌ Failed to send enrollment admin notification")

    return result


def send_course_completion_email(user, course, enrollment):
    """Send course completion congratulations email to user"""
    logger.info(f"Preparing to send course completion email to {user.email} for course {course.title}")

    # Calculate additional context data
    total_lessons = course.total_lessons
    completed_lessons = enrollment.lesson_progress.filter(status='completed').count()
    learning_streak = enrollment.get_learning_streak()

    # Calculate total study time from lesson progress
    total_study_time = enrollment.lesson_progress.aggregate(
        total_time=models.Sum('time_spent')
    )['total_time'] or 0

    context = {
        'user': user,
        'course': course,
        'enrollment': enrollment,
        'total_lessons': total_lessons,
        'completed_lessons': completed_lessons,
        'learning_streak': learning_streak,
        'total_study_time': total_study_time,
        'course_url': f"{settings.SITE_URL}/lms/courses/{course.slug}/" if hasattr(settings, 'SITE_URL') else f"/lms/courses/{course.slug}/",
        'certificate_url': f"{settings.SITE_URL}/lms/progress/certificates/" if hasattr(settings, 'SITE_URL') else "/lms/progress/certificates/",
        'support_email': settings.ADMIN_EMAIL,
        'site_name': 'Youth Impact Training Programme'
    }

    html_content = render_to_string('emails/course_completion.html', context)
    plain_content = render_to_string('emails/course_completion.txt', context)

    subject = f"🎉 Course Completed: {course.title} - Congratulations from YITP!"

    logger.info(f"Sending course completion email with subject: {subject}")

    result = send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user.email],
        plain_text_content=plain_content
    )

    if result:
        logger.info(f"✅ Course completion email sent successfully to {user.email}")
    else:
        logger.error(f"❌ Failed to send course completion email to {user.email}")

    return result


def send_certificate_issuance_email(user, course, certificate):
    """Send certificate issuance notification email to user"""
    logger.info(f"Preparing to send certificate issuance email to {user.email} for course {course.title}")

    # Get enrollment for additional context
    enrollment = certificate.enrollment

    # Calculate additional context data
    completed_lessons = enrollment.lesson_progress.filter(status='completed').count()
    learning_streak = enrollment.get_learning_streak()

    # Calculate total study time from lesson progress
    total_study_time = enrollment.lesson_progress.aggregate(
        total_time=models.Sum('time_spent')
    )['total_time'] or 0

    context = {
        'user': user,
        'course': course,
        'certificate': certificate,
        'enrollment': enrollment,
        'completed_lessons': completed_lessons,
        'learning_streak': learning_streak,
        'total_study_time': total_study_time,
        'certificate_download_url': f"{settings.SITE_URL}/lms/progress/certificates/{certificate.certificate_id}/download/" if hasattr(settings, 'SITE_URL') else f"/lms/progress/certificates/{certificate.certificate_id}/download/",
        'verification_url': f"{settings.SITE_URL}/certificates/verify/{certificate.verification_code}/" if hasattr(settings, 'SITE_URL') else f"/certificates/verify/{certificate.verification_code}/",
        'support_email': settings.ADMIN_EMAIL,
        'site_name': 'Youth Impact Training Programme'
    }

    html_content = render_to_string('emails/certificate_issuance.html', context)
    plain_content = render_to_string('emails/certificate_issuance.txt', context)

    subject = f"🎓 Your YITP Certificate is Ready: {course.title}"

    logger.info(f"Sending certificate issuance email with subject: {subject}")

    result = send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[user.email],
        plain_text_content=plain_content
    )

    if result:
        logger.info(f"✅ Certificate issuance email sent successfully to {user.email}")
    else:
        logger.error(f"❌ Failed to send certificate issuance email to {user.email}")

    return result


# ============================================================================
# COURSE CREATION NOTIFICATION SYSTEM
# ============================================================================

def send_course_creation_notification(instructor, course):
    """Send email notification to admin when instructor creates a course"""
    logger.info(f"Preparing to send course creation notification for course: {course.title}")

    context = {
        'instructor': instructor,
        'course': course,
        'instructor_name': instructor.get_full_name() or instructor.username,
        'course_title': course.title,
        'course_description': course.description,
        'difficulty_level': course.get_difficulty_level_display(),
        'estimated_duration': course.estimated_duration,
        'category': course.category.name if course.category else 'Uncategorized',
        'admin_url': f"https://www.youthimpactglobal.com/admin/courses/course/{course.id}/change/",
        'site_name': 'Youth Impact Training Programme',
        'admin_email': settings.ADMIN_EMAIL
    }

    # Admin notification email content
    subject = f"📚 New Course Created: {course.title} - Requires Review"

    admin_email_content = f"""
COURSE CREATION NOTIFICATION
Youth Impact Training Programme

A new course has been created and is awaiting your review and approval.

COURSE DETAILS:
• Title: {course.title}
• Instructor: {instructor.get_full_name() or instructor.username} ({instructor.email})
• Category: {course.category.name if course.category else 'Uncategorized'}
• Difficulty: {course.get_difficulty_level_display()}
• Duration: {course.estimated_duration} hours
• Status: In Review
• Created: {course.created_at.strftime('%B %d, %Y at %I:%M %p')}

DESCRIPTION:
{course.description}

INSTRUCTOR INFORMATION:
• Email: {instructor.email}
• Username: {instructor.username}
• Full Name: {instructor.get_full_name() or 'Not provided'}

ADMIN ACTIONS REQUIRED:
1. Review course content and structure
2. Verify instructor qualifications
3. Approve or reject the course
4. Provide feedback if needed

ADMIN PANEL ACCESS:
{context['admin_url']}

NEXT STEPS:
• Login to the admin panel
• Navigate to Courses → Course → {course.title}
• Review the course details
• Update status to 'Published' to approve
• Or update status to 'Rejected' with feedback

This course will remain in "In Review" status until you take action.

---
YITP Course Management System
Youth Impact Training Programme
"""

    logger.info(f"Sending course creation notification with subject: {subject}")

    # Send email to admin
    admin_email = getattr(settings, 'ADMIN_EMAIL', 'youthimpactglobal3@gmail.com')
    result = send_html_email(
        subject=subject,
        html_content=admin_email_content,  # Using plain text as HTML for simplicity
        recipient_list=[admin_email],
        plain_text_content=admin_email_content
    )

    if result:
        logger.info(f"✅ Course creation notification sent successfully for course: {course.title}")
    else:
        logger.error(f"❌ Failed to send course creation notification for course: {course.title}")

    return result


# ============================================================================
# INSTRUCTOR WELCOME EMAIL SYSTEM
# ============================================================================

def send_instructor_welcome_email(user, instructor_profile, temporary_password=None, created_by_admin=None):
    """
    Send comprehensive welcome email to newly created instructor accounts

    Args:
        user: User instance for the new instructor
        instructor_profile: InstructorProfile instance with role and permissions
        temporary_password: Optional temporary password if generated
        created_by_admin: User instance of the admin who created the account

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Validate email address
    if not user.email or not user.email.strip():
        logger.error(f"❌ Cannot send instructor welcome email: User {user.username} has no email address")
        return False

    logger.info(f"Preparing to send instructor welcome email to {user.email}")

    try:
        # Get role-specific information
        role_colors = {
            'system_admin': '#dc3545',  # Red
            'course_instructor': '#ff5d15',  # YITP Orange
            'teaching_assistant': '#28a745',  # Green
            'content_manager': '#17a2b8',  # Cyan
            'accountant': '#6f42c1',  # Purple
            'grader': '#6c757d',  # Gray
        }

        # Build permissions summary based on role
        permissions_summary = []
        if instructor_profile.instructor_role == 'system_admin':
            permissions_summary = [
                "Full system administration access",
                "All course and user management permissions",
                "Complete access to admin interface",
                "System configuration and settings management"
            ]
        elif instructor_profile.instructor_role == 'course_instructor':
            permissions_summary = [
                "Create and manage courses",
                "Create and manage course modules and lessons",
                "Create and manage quizzes and assessments",
                "View and manage student enrollments",
                "Access to instructor admin interface"
            ]
        elif instructor_profile.instructor_role == 'teaching_assistant':
            permissions_summary = [
                "View course content and materials",
                "Modify course modules and lessons",
                "Grade quizzes and assessments",
                "Manage student enrollments and progress",
                "Limited admin interface access"
            ]
        elif instructor_profile.instructor_role == 'content_manager':
            permissions_summary = [
                "Create and manage course content",
                "Create and manage course modules and lessons",
                "Create and manage quizzes and assessments",
                "View student enrollment information",
                "Access to content management admin interface"
            ]
        elif instructor_profile.instructor_role == 'accountant':
            permissions_summary = [
                "Full visibility into payment records",
                "Review and verify sponsorship applications",
                "Export finance and billing reports",
                "Access to finance-specific dashboards"
            ]
        elif instructor_profile.instructor_role == 'grader':
            permissions_summary = [
                "View course content and materials",
                "Grade quizzes and assessments",
                "View and update student progress",
                "Limited admin interface access"
            ]

        # Build URLs
        base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        login_url = f"{base_url}/login/"
        admin_url = f"{base_url}/admin/"
        instructor_dashboard_url = f"{base_url}/users/instructor/"
        resources_url = f"{base_url}/users/instructor/tutorial/"
        profile_url = f"{base_url}/profile/"

        # Generate magic link for automatic login
        magic_link_url = None
        try:
            from .magic_link_utils import generate_magic_link_url
            magic_link_url, magic_token = generate_magic_link_url(
                user=user,
                purpose='instructor_welcome',
                expiry_days=10
            )
            logger.info(f"Generated magic link for instructor {user.username}")
        except Exception as e:
            logger.error(f"Failed to generate magic link for instructor {user.username}: {str(e)}")
            # Continue without magic link if generation fails

        # Email context
        context = {
            'user': user,
            'instructor_profile': instructor_profile,
            'instructor_role_display': instructor_profile.get_instructor_role_display(),
            'verification_status': instructor_profile.verification_status,
            'role_color': role_colors.get(instructor_profile.instructor_role, '#6c757d'),
            'permissions_summary': permissions_summary,
            'can_access_admin': instructor_profile.can_access_admin,
            'temporary_password': temporary_password,
            'login_url': login_url,
            'admin_url': admin_url,
            'instructor_dashboard_url': instructor_dashboard_url,
            'resources_url': resources_url,
            'profile_url': profile_url,
            'magic_link_url': magic_link_url,  # Add magic link to context
            'support_email': getattr(settings, 'ADMIN_EMAIL', 'youthimpactglobal3@gmail.com'),
            'created_by_admin': created_by_admin,
            'site_name': 'Youth Impact Training Programme'
        }

        # Render email templates
        html_content = render_to_string('emails/instructor_welcome.html', context)
        plain_content = render_to_string('emails/instructor_welcome.txt', context)

        # Email subject
        role_display = instructor_profile.get_instructor_role_display()
        subject = f"Welcome to YITP Instructor Team - {role_display} Account Created"

        logger.info(f"Sending instructor welcome email with subject: {subject}")

        # Send email
        result = send_html_email(
            subject=subject,
            html_content=html_content,
            recipient_list=[user.email],
            plain_text_content=plain_content
        )

        if result:
            logger.info(f"✅ Successfully sent instructor welcome email to {user.email}")

            # Log the email delivery for audit purposes
            try:
                # Create audit log entry
                audit_message = (
                    f"Instructor welcome email sent to {user.email} "
                    f"(Role: {role_display}, Created by: {created_by_admin.username if created_by_admin else 'System'})"
                )
                logger.info(f"AUDIT: {audit_message}")
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {str(audit_error)}")
        else:
            logger.error(f"❌ Failed to send instructor welcome email to {user.email}")

        return result

    except Exception as e:
        logger.error(f"❌ Error sending instructor welcome email to {user.email}: {str(e)}")
        return False


def send_instructor_login_notification(user, login_timestamp=None, ip_address=None, user_agent=None):
    """
    Send notification to admin when instructor logs in for security monitoring

    Args:
        user: User instance of the instructor who logged in
        login_timestamp: Timestamp of login (defaults to now)
        ip_address: IP address of the login attempt
        user_agent: User agent string from the request

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if login_timestamp is None:
        login_timestamp = timezone.now()

    # Only send notifications for instructor accounts
    try:
        instructor_profile = user.instructor_profile
    except:
        # Not an instructor, skip notification
        return False

    logger.info(f"Preparing to send instructor login notification for {user.username}")

    try:
        # Email context
        context = {
            'instructor_user': user,
            'instructor_profile': instructor_profile,
            'login_timestamp': login_timestamp,
            'ip_address': ip_address or 'Unknown',
            'user_agent': user_agent or 'Unknown',
            'instructor_role_display': instructor_profile.get_instructor_role_display(),
            'verification_status': instructor_profile.get_verification_status_display(),
            'admin_email': getattr(settings, 'ADMIN_EMAIL', 'youthimpactglobal3@gmail.com'),
            'site_name': 'Youth Impact Training Programme',
            'login_location': f"{ip_address}" if ip_address else "Unknown Location"
        }

        # Email subject
        subject = f"YITP Instructor Login Alert - {user.get_full_name() or user.username}"

        # Simple text email for admin notification
        email_content = f"""
YITP INSTRUCTOR LOGIN NOTIFICATION

An instructor has logged into the YITP Learning Management System.

INSTRUCTOR DETAILS:
• Name: {user.get_full_name() or user.username}
• Username: {user.username}
• Email: {user.email}
• Role: {instructor_profile.get_instructor_role_display()}
• Verification Status: {instructor_profile.get_verification_status_display()}

LOGIN DETAILS:
• Login Time: {login_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
• IP Address: {ip_address or 'Unknown'}
• User Agent: {user_agent or 'Unknown'}
• Last Login: {user.last_login.strftime('%Y-%m-%d %H:%M:%S UTC') if user.last_login else 'First time login'}

SECURITY INFORMATION:
• Account Status: {'Active' if user.is_active else 'Inactive'}
• Staff Status: {'Yes' if user.is_staff else 'No'}
• Superuser: {'Yes' if user.is_superuser else 'No'}

This is an automated security notification. If this login was not authorized, please take immediate action to secure the account.

---
YITP Security Monitoring System
Youth Impact Training Programme
"""

        logger.info(f"Sending instructor login notification with subject: {subject}")

        # Send email to admin
        admin_email = getattr(settings, 'ADMIN_EMAIL', 'youthimpactglobal3@gmail.com')
        result = send_html_email(
            subject=subject,
            html_content=email_content,  # Using plain text as HTML for simplicity
            recipient_list=[admin_email],
            plain_text_content=email_content
        )

        if result:
            logger.info(f"✅ Successfully sent instructor login notification to {admin_email}")

            # Log for audit purposes
            audit_message = (
                f"Instructor login notification sent to admin for {user.username} "
                f"(Role: {instructor_profile.get_instructor_role_display()}, IP: {ip_address or 'Unknown'})"
            )
            logger.info(f"AUDIT: {audit_message}")
        else:
            logger.error(f"❌ Failed to send instructor login notification to {admin_email}")

        return result

    except Exception as e:
        logger.error(f"❌ Error sending instructor login notification for {user.username}: {str(e)}")
        return False


def send_otp_verification_admin_notification(user, verification_timestamp=None):
    """Send notification to admin when user completes OTP verification"""
    if verification_timestamp is None:
        verification_timestamp = timezone.now()

    # Get user profile information if available
    try:
        user_profile = user.profile
    except:
        user_profile = None

    context = {
        'user': user,
        'user_profile': user_profile,
        'verification_timestamp': verification_timestamp,
        'site_name': 'Youth Impact Training Programme',
        'admin_url': f"{settings.SITE_URL}/admin/auth/user/{user.id}/change/" if hasattr(settings, 'SITE_URL') else f"/admin/auth/user/{user.id}/change/",
        'user_dashboard_url': f"{settings.SITE_URL}/lms/dashboard/" if hasattr(settings, 'SITE_URL') else '/lms/dashboard/'
    }

    html_content = render_to_string('emails/otp_verification_admin_notification.html', context)
    plain_content = render_to_string('emails/otp_verification_admin_notification.txt', context)

    subject = f"New User Verified: {user.get_full_name() or user.username} - YITP"

    logger.info(f"Sending OTP verification admin notification for user: {user.email}")

    result = send_html_email(
        subject=subject,
        html_content=html_content,
        recipient_list=[settings.ADMIN_EMAIL],
        plain_text_content=plain_content
    )

    if result:
        logger.info(f"✅ OTP verification admin notification sent successfully for user: {user.email}")
    else:
        logger.error(f"❌ Failed to send OTP verification admin notification for user: {user.email}")

    return result
