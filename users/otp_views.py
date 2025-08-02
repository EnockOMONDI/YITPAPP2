"""
OTP verification views for YITP application
Handles OTP generation, sending, and verification with enhanced error handling and UX
"""
import logging
import json
import re
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import OTPVerification, Profile
from .email_utils import generate_otp, send_otp_email, send_welcome_email

# Configure logging
logger = logging.getLogger(__name__)

# OTP Error Types for Enhanced Error Messaging
class OTPError:
    INVALID_FORMAT = "invalid_format"
    EXPIRED = "expired"
    ALREADY_USED = "already_used"
    NOT_FOUND = "not_found"
    USER_NOT_FOUND = "user_not_found"
    MULTIPLE_ATTEMPTS = "multiple_attempts"
    SYSTEM_ERROR = "system_error"

# Enhanced Error Messages
OTP_ERROR_MESSAGES = {
    OTPError.INVALID_FORMAT: {
        'message': 'Invalid OTP format. Please enter exactly 6 digits.',
        'help': 'OTP codes contain only numbers (0-9) and are exactly 6 digits long.',
        'type': 'format'
    },
    OTPError.EXPIRED: {
        'message': 'OTP code has expired. Please request a new verification code.',
        'help': 'OTP codes expire after 200 minutes for security reasons.',
        'type': 'expired'
    },
    OTPError.ALREADY_USED: {
        'message': 'This OTP code has already been used. Please request a new verification code.',
        'help': 'Each OTP code can only be used once for security.',
        'type': 'used'
    },
    OTPError.NOT_FOUND: {
        'message': 'Invalid OTP code. Please check your code and try again.',
        'help': 'Make sure you entered the code exactly as received in your email.',
        'type': 'invalid'
    },
    OTPError.USER_NOT_FOUND: {
        'message': 'User verification session not found. Please restart the registration process.',
        'help': 'Your verification session may have expired.',
        'type': 'session'
    },
    OTPError.MULTIPLE_ATTEMPTS: {
        'message': 'Too many failed attempts. Please wait before trying again.',
        'help': 'For security, please wait a moment before attempting verification again.',
        'type': 'attempts'
    },
    OTPError.SYSTEM_ERROR: {
        'message': 'System error during verification. Please try again.',
        'help': 'If the problem persists, please contact support.',
        'type': 'system'
    }
}

def generate_and_send_otp(user):
    """Generate and send OTP to user"""
    # Invalidate any existing OTPs for this user
    OTPVerification.objects.filter(user=user, is_used=False).update(is_used=True)
    
    # Generate new OTP
    otp_code = generate_otp(length=getattr(settings, 'OTP_LENGTH', 6))
    
    # Calculate expiry time
    expiry_minutes = getattr(settings, 'OTP_EXPIRY_MINUTES', 200)
    expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
    
    # Create OTP record
    otp_record = OTPVerification.objects.create(
        user=user,
        otp_code=otp_code,
        expires_at=expires_at
    )
    
    # Send OTP email
    email_sent = send_otp_email(user, otp_code)
    
    return otp_record, email_sent

def validate_otp_format(otp_code):
    """Validate OTP code format"""
    if not otp_code:
        return False, OTPError.INVALID_FORMAT

    # Remove any spaces, dashes, or other non-digit characters
    cleaned_code = re.sub(r'[^0-9]', '', otp_code)

    # Check if it's exactly 6 digits
    if len(cleaned_code) != 6 or not cleaned_code.isdigit():
        return False, OTPError.INVALID_FORMAT

    return True, cleaned_code

def get_otp_error_details(error_type, user=None, otp_code=None):
    """Get detailed error information for OTP verification failures"""
    error_info = OTP_ERROR_MESSAGES.get(error_type, OTP_ERROR_MESSAGES[OTPError.SYSTEM_ERROR])

    # Add contextual information for logging
    context = {
        'user_id': user.id if user else None,
        'username': user.username if user else None,
        'otp_code_length': len(otp_code) if otp_code else 0,
        'timestamp': timezone.now().isoformat()
    }

    return error_info, context

def verify_otp_view(request):
    """Enhanced OTP verification with detailed error handling and logging"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        otp_code = request.POST.get('otp_code', '').strip()

        # Enhanced logging for debugging
        logger.info(f"OTP verification attempt: user_id={user_id}, code_length={len(otp_code) if otp_code else 0}")

        # Validate required fields
        if not user_id or not otp_code:
            error_info, context = get_otp_error_details(OTPError.INVALID_FORMAT)
            logger.warning(f"OTP verification failed - missing fields: {context}")
            messages.error(request, error_info['message'])
            return render(request, 'users/verify_otp.html', {
                'user_id': user_id,
                'error_type': error_info['type'],
                'error_help': error_info['help']
            })

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            error_info, context = get_otp_error_details(OTPError.USER_NOT_FOUND)
            logger.error(f"OTP verification failed - user not found: user_id={user_id}")
            messages.error(request, error_info['message'])
            return redirect('users:register')

        # Validate OTP format
        is_valid_format, cleaned_code_or_error = validate_otp_format(otp_code)
        if not is_valid_format:
            error_info, context = get_otp_error_details(cleaned_code_or_error, user, otp_code)
            logger.warning(f"OTP verification failed - invalid format: {context}")
            messages.error(request, error_info['message'])
            return render(request, 'users/verify_otp.html', {
                'user_id': user_id,
                'error_type': error_info['type'],
                'error_help': error_info['help']
            })

        cleaned_otp_code = cleaned_code_or_error

        # Check for existing OTP record with detailed error analysis
        current_time = timezone.now()

        # First, check if OTP exists at all
        otp_exists = OTPVerification.objects.filter(
            user=user,
            otp_code=cleaned_otp_code
        ).first()

        if not otp_exists:
            error_info, context = get_otp_error_details(OTPError.NOT_FOUND, user, cleaned_otp_code)
            logger.warning(f"OTP verification failed - code not found: {context}")
            messages.error(request, error_info['message'])
            return render(request, 'users/verify_otp.html', {
                'user_id': user_id,
                'error_type': error_info['type'],
                'error_help': error_info['help']
            })

        # Check if OTP is already used
        if otp_exists.is_used:
            error_info, context = get_otp_error_details(OTPError.ALREADY_USED, user, cleaned_otp_code)
            logger.warning(f"OTP verification failed - already used: {context}")
            messages.error(request, error_info['message'])
            return render(request, 'users/verify_otp.html', {
                'user_id': user_id,
                'error_type': error_info['type'],
                'error_help': error_info['help']
            })

        # Check if OTP is expired
        if otp_exists.expires_at <= current_time:
            error_info, context = get_otp_error_details(OTPError.EXPIRED, user, cleaned_otp_code)
            logger.warning(f"OTP verification failed - expired: {context}")
            messages.error(request, error_info['message'])
            return render(request, 'users/verify_otp.html', {
                'user_id': user_id,
                'error_type': error_info['type'],
                'error_help': error_info['help'],
                'show_resend': True
            })

        # OTP is valid - proceed with verification
        try:
            with transaction.atomic():
                # Mark OTP as used and verified
                otp_exists.is_used = True
                otp_exists.is_verified = True
                otp_exists.save()

                # Mark user as active if not already
                if not user.is_active:
                    user.is_active = True
                    user.save()

                # Create or update profile with email verification status
                try:
                    profile = user.profile
                    profile.email_verified = True
                    profile.update_profile_completion()
                    profile.save()
                except Profile.DoesNotExist:
                    profile = Profile.objects.create(user=user, email_verified=True)
                    profile.update_profile_completion()

                # Send welcome email
                send_welcome_email(user)

                # Send admin notification
                try:
                    from users.email_utils import send_otp_verification_admin_notification
                    send_otp_verification_admin_notification(user)
                except Exception as e:
                    logger.error(f"Failed to send admin notification for user {user.email}: {str(e)}")

                # Log successful verification
                logger.info(f"OTP verification successful: user_id={user.id}, username={user.username}")

                # Automatically log in the user
                login(request, user)

                # Set session flags
                request.session['just_completed_otp_verification'] = True
                request.session['otp_verification_timestamp'] = timezone.now().isoformat()

                messages.success(request, 'Email verified successfully! You are now logged in. Welcome to YITP!')
                return redirect('yitp:welcome')

        except Exception as e:
            error_info, context = get_otp_error_details(OTPError.SYSTEM_ERROR, user, cleaned_otp_code)
            logger.error(f"OTP verification system error: {context}, error: {str(e)}")
            messages.error(request, error_info['message'])
            return render(request, 'users/verify_otp.html', {
                'user_id': user_id,
                'error_type': error_info['type'],
                'error_help': error_info['help']
            })

    # GET request - handle auto-fill from email link
    user_id = request.GET.get('user_id')
    auto_fill_code = request.GET.get('code')  # OTP code from email link

    context = {
        'user_id': user_id,
        'auto_fill_code': auto_fill_code,
        'from_email_link': bool(auto_fill_code)  # Flag to show user came from email
    }

    # If we have both user_id and code, show helpful message
    if user_id and auto_fill_code:
        try:
            user = User.objects.get(id=user_id)
            messages.info(
                request,
                f"Welcome back! We've pre-filled your verification code from the email link. "
                f"Simply click 'Verify' to complete your registration."
            )
        except User.DoesNotExist:
            messages.error(request, "Invalid verification link. Please try registering again.")
            return redirect('users:register')

    return render(request, 'users/verify_otp.html', context)

def resend_otp_view(request):
    """Resend OTP to user"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        
        if not user_id:
            return JsonResponse({'success': False, 'message': 'User ID required'})
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Invalid user'})
        
        # Check if user already verified
        if user.is_active and OTPVerification.objects.filter(user=user, is_verified=True).exists():
            return JsonResponse({'success': False, 'message': 'User already verified'})
        
        # Generate and send new OTP
        otp_record, email_sent = generate_and_send_otp(user)
        
        if email_sent:
            return JsonResponse({
                'success': True, 
                'message': f'New OTP sent to {user.email}',
                'expiry_minutes': settings.OTP_EXPIRY_MINUTES
            })
        else:
            return JsonResponse({'success': False, 'message': 'Failed to send OTP email'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def otp_status_view(request):
    """Check OTP verification status for current user"""
    user = request.user
    
    # Check if user has verified OTP
    verified_otp = OTPVerification.objects.filter(user=user, is_verified=True).first()
    
    # Get latest OTP (verified or not)
    latest_otp = OTPVerification.objects.filter(user=user).order_by('-created_at').first()
    
    context = {
        'user': user,
        'is_verified': bool(verified_otp),
        'latest_otp': latest_otp,
        'verified_otp': verified_otp
    }
    
    return render(request, 'users/otp_status.html', context)

def check_otp_required(user):
    """Check if user needs OTP verification"""
    # Check if user has any verified OTP
    return not OTPVerification.objects.filter(user=user, is_verified=True).exists()

def send_otp_for_registration(user):
    """Send OTP for new user registration"""
    # Set user as inactive until OTP verification
    user.is_active = False
    user.save()

    # Generate and send OTP
    otp_record, email_sent = generate_and_send_otp(user)

    return otp_record, email_sent

def check_database_consistency():
    """Check database consistency after SQLite migration"""
    issues = []

    try:
        # Check for orphaned OTP records
        orphaned_otps = OTPVerification.objects.filter(user__isnull=True)
        if orphaned_otps.exists():
            issues.append(f"Found {orphaned_otps.count()} orphaned OTP records")
            logger.warning(f"Database consistency issue: {orphaned_otps.count()} orphaned OTP records")

        # Check for users without profiles
        users_without_profiles = User.objects.filter(profile__isnull=True)
        if users_without_profiles.exists():
            issues.append(f"Found {users_without_profiles.count()} users without profiles")
            logger.warning(f"Database consistency issue: {users_without_profiles.count()} users without profiles")

            # Auto-create missing profiles
            for user in users_without_profiles:
                try:
                    Profile.objects.create(user=user)
                    logger.info(f"Created missing profile for user {user.username}")
                except Exception as e:
                    logger.error(f"Failed to create profile for user {user.username}: {str(e)}")

        # Check for expired but unused OTP records
        expired_unused_otps = OTPVerification.objects.filter(
            is_used=False,
            expires_at__lt=timezone.now()
        )
        if expired_unused_otps.exists():
            count = expired_unused_otps.count()
            issues.append(f"Found {count} expired unused OTP records")
            logger.info(f"Database cleanup: {count} expired unused OTP records found")

        # Check for duplicate OTP records for same user
        from django.db.models import Count
        duplicate_otps = OTPVerification.objects.values('user', 'otp_code').annotate(
            count=Count('id')
        ).filter(count__gt=1)

        if duplicate_otps.exists():
            issues.append(f"Found {duplicate_otps.count()} duplicate OTP records")
            logger.warning(f"Database consistency issue: {duplicate_otps.count()} duplicate OTP records")

        if not issues:
            logger.info("Database consistency check passed - no issues found")
            return True, "Database consistency check passed"
        else:
            return False, issues

    except Exception as e:
        logger.error(f"Database consistency check failed: {str(e)}")
        return False, [f"Consistency check error: {str(e)}"]
