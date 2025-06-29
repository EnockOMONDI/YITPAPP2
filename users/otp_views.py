"""
OTP verification views for YITP application
Handles OTP generation, sending, and verification
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from .models import OTPVerification
from .email_utils import generate_otp, send_otp_email, send_welcome_email

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

def verify_otp_view(request):
    """Handle OTP verification"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not user_id or not otp_code:
            messages.error(request, 'Please provide both user ID and OTP code.')
            return render(request, 'users/verify_otp.html')
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, 'Invalid user.')
            return render(request, 'users/verify_otp.html')
        
        # Find valid OTP
        otp_record = OTPVerification.objects.filter(
            user=user,
            otp_code=otp_code,
            is_used=False,
            expires_at__gt=timezone.now()
        ).first()
        
        if otp_record:
            # Mark OTP as used and verified
            otp_record.is_used = True
            otp_record.is_verified = True
            otp_record.save()
            
            # Mark user as active if not already
            if not user.is_active:
                user.is_active = True
                user.save()
            
            # Send welcome email
            send_welcome_email(user)

            messages.success(request, 'Email verified successfully! Welcome to YITP!')
            return redirect('yitp:welcome')
        else:
            messages.error(request, 'Invalid or expired OTP code. Please try again.')
    
    # GET request or failed POST
    user_id = request.GET.get('user_id')
    context = {'user_id': user_id}
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
