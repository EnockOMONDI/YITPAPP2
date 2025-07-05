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
from django.db import models
import logging

logger = logging.getLogger(__name__)

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_html_email_direct(subject, html_content, recipient_list, from_email=None, plain_text_content=None):
    """
    Send HTML email directly using smtplib with SSL context handling
    This bypasses Django's email backend SSL issues
    """
    import smtplib
    import ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    try:
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL

        if plain_text_content is None:
            plain_text_content = strip_tags(html_content)

        logger.info(f"Attempting to send email directly to {recipient_list}")
        logger.info(f"Subject: {subject}")
        logger.info(f"From: {from_email}")

        # Create unverified SSL context to handle certificate issues
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Connect to Gmail SMTP
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls(context=context)
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

        # Create multipart message
        msg = MIMEMultipart('alternative')
        msg['From'] = from_email
        msg['Subject'] = subject

        # Add plain text and HTML parts
        part1 = MIMEText(plain_text_content, 'plain')
        part2 = MIMEText(html_content, 'html')

        msg.attach(part1)
        msg.attach(part2)

        # Send to each recipient
        for recipient in recipient_list:
            msg['To'] = recipient
            server.send_message(msg)
            del msg['To']  # Remove To header for next recipient

        server.quit()

        logger.info(f"✅ Email sent successfully to {recipient_list}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to send email to {recipient_list}: {str(e)}")
        return False

def send_html_email(subject, html_content, recipient_list, from_email=None, plain_text_content=None):
    """
    Send HTML email with fallback to plain text
    Uses direct SMTP method as primary, Django backend as fallback
    """
    # Try direct method first (more reliable)
    if send_html_email_direct(subject, html_content, recipient_list, from_email, plain_text_content):
        return True

    # Fallback to Django's email backend
    logger.warning("Direct email failed, trying Django backend...")

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
            logger.info(f"✅ Email sent via Django backend to {recipient_list}")
            return True
        else:
            logger.warning(f"⚠️ Django backend returned 0 for {recipient_list}")
            return False

    except Exception as e:
        logger.error(f"❌ Django backend also failed for {recipient_list}: {str(e)}")
        return False

def test_email_configuration():
    """
    Test email configuration by sending a test email
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
    """Send OTP verification email to user"""
    logger.info(f"Preparing to send OTP email to {user.email}")

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


def send_enrollment_confirmation_email(user, course, enrollment):
    """Send enrollment confirmation email to user"""
    logger.info(f"Preparing to send enrollment confirmation email to {user.email} for course {course.title}")

    context = {
        'user': user,
        'course': course,
        'enrollment_date': enrollment.enrollment_date,
        'course_url': f"{settings.SITE_URL}/lms/courses/{course.slug}/" if hasattr(settings, 'SITE_URL') else f"/lms/courses/{course.slug}/",
        'support_email': settings.ADMIN_EMAIL,
        'site_name': 'Youth Impact Training Programme'
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


def send_enrollment_admin_notification(user, course, enrollment):
    """Send enrollment notification email to admin"""
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
        'site_name': 'Youth Impact Training Programme'
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
