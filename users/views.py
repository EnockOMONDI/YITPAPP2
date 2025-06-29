from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from . models import Editpage,SecondSection,SecondSectionIcon,SecondSectionBox, SponsorshipRequest, Profile
from .forms import SponsorshipRequestForm
from .otp_views import send_otp_for_registration
from .email_utils import send_login_notification, send_sponsorship_confirmation_email, send_sponsorship_admin_notification, test_email_configuration, send_html_email

from django.shortcuts import render,redirect,HttpResponse
from django.http import Http404


def home(request):
    # Fetch all the sections from the database based on the section names
    hnew = Editpage.objects.filter(section_name='hnew').first()
    hneww = Editpage.objects.filter(section_name='hneww').first()
    hnewww = Editpage.objects.filter(section_name='hnewww').first()
    Programme1 = Editpage.objects.filter(section_name='Programme1').first()
    Programme2 = Editpage.objects.filter(section_name='Programme2').first()
    Programme3 = Editpage.objects.filter(section_name='Programme3').first()
    about_us = Editpage.objects.filter(section_name='about_us').first()
    mission = Editpage.objects.filter(section_name='mission').first()
    vision = Editpage.objects.filter(section_name='vision').first()
    volunteer = Editpage.objects.filter(section_name='Volunteer').first()
    footer = Editpage.objects.filter(section_name='footer').first()
    team1 = Editpage.objects.filter(section_name='team1').first()
    team2 = Editpage.objects.filter(section_name='team2').first()
    team3 = Editpage.objects.filter(section_name='team3').first()
    home_section = Editpage.objects.filter(section_name='home_section').first()
    second_section = SecondSection.objects.first()
    second_section_icons = SecondSectionIcon.objects.all().order_by('order')
    second_section_box = SecondSectionBox.objects.first()

    # Add all the variables to the context dictionary
    content = {
        'Programme1': Programme1,
        'Programme2': Programme2,
        'Programme3': Programme3,
        'hnew': hnew,
        'hneww': hneww,
        'hnewww': hnewww,
        'about_us': about_us,
        'mission': mission,
        'vision': vision,
        'volunteer': volunteer,
        'footer': footer,
        'team1': team1,
        'team2': team2,
        'team3': team3,
        'second_section': second_section ,
        'second_section_icons': second_section_icons,
        'second_section_box': second_section_box,
        
        
    }

    return render(request, 'index.html', content)

def aboutus(request):
    aboutUs = Editpage.objects.filter(section_name='aboutUs').first()
    footer = Editpage.objects.filter(section_name='footer').first()
    volunteer = Editpage.objects.filter(section_name='Volunteer').first()
    content = {
        'volunteer': volunteer,
        'footer': footer,
        'aboutUs': aboutUs,
        
    }
    
    return render(request, 'aboutus.html', content)

def programs(request):
    footer = Editpage.objects.filter(section_name='footer').first()
    our_programs = Editpage.objects.filter(section_name='our_Programs').first()
    reach = Editpage.objects.filter(section_name='reach').first()
    volunteer = Editpage.objects.filter(section_name='Volunteer').first()

    content = {
        'our_programs': our_programs,
        'footer': footer,
        'reach': reach,
        'volunteer': volunteer,
       
    }
    return render(request, 'programs.html', content)

def ourteam(request):
    volunteer = Editpage.objects.filter(section_name='Volunteer').first()
    footer = Editpage.objects.filter(section_name='footer').first()
    team1 = Editpage.objects.filter(section_name='team1').first()
    team2 = Editpage.objects.filter(section_name='team2').first()
    team3 = Editpage.objects.filter(section_name='team3').first()
    content = {
       
        'volunteer': volunteer,
        'footer': footer,
        'team1': team1,
        'team2': team2,
        'team3': team3,
     
    }
    
    return render(request, 'ourteam.html', content)

def contactus(request):
    
    return render(request, 'contactus.html')

# Create your views here.
def register(request):
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            terms = request.POST.get('terms')

            # Validation
            errors = []

            # Check required fields
            if not all([first_name, last_name, username, email, password1, password2]):
                errors.append('All fields are required.')

            # Check terms acceptance
            if not terms:
                errors.append('You must agree to the Terms of Service and Privacy Policy.')

            # Validate email format
            if email:
                try:
                    validate_email(email)
                except ValidationError:
                    errors.append('Please enter a valid email address.')

            # Check password match
            if password1 != password2:
                errors.append('Passwords do not match.')

            # Validate password strength
            if password1:
                try:
                    validate_password(password1)
                except ValidationError as e:
                    errors.extend(e.messages)

            # Check if username exists
            if username and User.objects.filter(username=username).exists():
                errors.append('Username already taken. Please choose a different username.')

            # Check if email exists
            if email and User.objects.filter(email=email).exists():
                errors.append('Email already registered. Please use a different email or sign in.')

            # Validate phone number format (optional field)
            if phone_number:
                # Remove any non-digit characters for validation
                phone_digits = ''.join(filter(str.isdigit, phone_number))
                if len(phone_digits) < 10:
                    errors.append('Please enter a valid phone number with at least 10 digits.')

            # If there are errors, show them
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'signup.html')

            # Create user (inactive until OTP verification)
            user = User.objects.create_user(
                username=username,
                password=password1,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=False  # User will be activated after OTP verification
            )
            user.save()

            # Create user profile with phone number
            # Use get_or_create to handle potential race conditions with signals
            profile, created = Profile.objects.get_or_create(user=user)
            if phone_number:
                profile.phone_number = phone_number
                profile.save()

            # Send OTP for email verification
            try:
                otp_record, email_sent = send_otp_for_registration(user)
                if email_sent:
                    messages.success(
                        request,
                        f'Account created successfully! We\'ve sent a verification code to {email}. '
                        'Please check your email and enter the code to complete your registration.'
                    )
                    return redirect(f'/verify-otp/?user_id={user.id}')
                else:
                    # If email sending fails, activate user and proceed normally
                    user.is_active = True
                    user.save()
                    messages.warning(
                        request,
                        'Account created successfully! However, we couldn\'t send the verification email. '
                        'Your account is now active.'
                    )
                    return redirect('login')
            except Exception as e:
                # If OTP system fails, activate user and proceed normally
                user.is_active = True
                user.save()
                messages.warning(
                    request,
                    'Account created successfully! Email verification is temporarily unavailable. '
                    'Your account is now active.'
                )
                return redirect('login')

        except Exception as e:
            messages.error(request, 'An error occurred during registration. Please try again.')
            return render(request, 'signup.html')
    else:
        return render(request, 'signup.html')

def login(request):
    # Redirect if user is already logged in
    if request.user.is_authenticated:
        return redirect('yitp:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember')

        # Basic validation
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'registration/login.html')

        # Try to authenticate with username first
        user = auth.authenticate(username=username, password=password)

        # If username authentication fails, try with email
        if user is None:
            try:
                user_obj = User.objects.get(email=username)
                user = auth.authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user is not None:
            if user.is_active:
                auth.login(request, user)

                # Send login notification email
                try:
                    send_login_notification(user, request)
                except Exception as e:
                    # Don't fail login if email notification fails
                    pass

                # Handle remember me functionality
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes

                # Get next URL or redirect to home
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                else:
                    messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                    return redirect('yitp:home')
            else:
                messages.error(request, 'Your account has been disabled. Please contact support.')
                return render(request, 'registration/login.html')
        else:
            messages.error(request, 'Invalid username/email or password. Please try again.')
            return render(request, 'registration/login.html')
    else:
        return render(request, 'registration/login.html')

def logout(request):
    if request.user.is_authenticated:
        username = request.user.first_name or request.user.username
        auth.logout(request)
        messages.success(request, f'Goodbye {username}! You have been successfully logged out.')
    return render(request, 'registration/logged_out.html')

@login_required
def unified_profile(request, section='overview'):
    """
    Unified profile view with multiple sections combining main profile and LMS functionality
    """
    from progress.models import Enrollment, LessonProgress, Achievement, StudySession
    from django.db.models import Sum, Count, Avg
    from datetime import datetime, timedelta

    user = request.user

    # Get or create user profile
    try:
        profile = user.profile
    except:
        profile, created = Profile.objects.get_or_create(user=user)

    # Base context
    context = {
        'user': user,
        'profile': profile,
        'active_section': section,
    }

    # Get user enrollments with related data
    enrollments = Enrollment.objects.filter(student=user).select_related('course').prefetch_related('lesson_progress')
    context['enrollments'] = enrollments

    # Basic statistics
    context['total_enrollments'] = enrollments.count()
    context['completed_courses'] = enrollments.filter(status='completed').count()
    context['active_courses'] = enrollments.filter(status='active').count()
    context['dropped_courses'] = enrollments.filter(status='dropped').count()

    # Learning analytics for LMS sections
    if section in ['overview', 'lms', 'courses', 'analytics']:
        # Total learning time from lesson progress
        total_time_seconds = LessonProgress.objects.filter(
            enrollment__student=user
        ).aggregate(total_time=Sum('time_spent'))['total_time'] or 0
        context['total_learning_hours'] = round(total_time_seconds / 3600, 1)

        # Study sessions analytics
        study_sessions = StudySession.objects.filter(student=user)
        context['total_study_sessions'] = study_sessions.count()

        # Learning streak calculation
        recent_activity = LessonProgress.objects.filter(
            enrollment__student=user,
            completed_at__isnull=False
        ).order_by('-completed_at')

        context['learning_streak'] = calculate_learning_streak(recent_activity)

        # Recent achievements
        recent_achievements = Achievement.objects.filter(student=user).order_by('-earned_at')[:5]
        context['recent_achievements'] = recent_achievements
        context['total_achievements'] = Achievement.objects.filter(student=user).count()

        # Course progress details
        course_progress = []
        for enrollment in enrollments:
            progress_data = {
                'enrollment': enrollment,
                'course': enrollment.course,
                'progress_percentage': enrollment.progress_percentage,
                'total_lessons': enrollment.course.total_lessons,
                'completed_lessons': enrollment.lesson_progress.filter(status='completed').count(),
                'last_accessed': enrollment.last_accessed,
                'can_continue': enrollment.lesson_progress.filter(status__in=['not_started', 'in_progress']).exists(),
                'next_lesson': enrollment.lesson_progress.filter(status__in=['not_started', 'in_progress']).first(),
            }
            course_progress.append(progress_data)
        context['course_progress'] = course_progress

        # Recent activity
        context['recent_activity'] = get_recent_activity(user)

    # Payment history for billing section
    if section in ['overview', 'billing']:
        context['payment_history'] = get_payment_history(user)

    # Sponsorship requests for overview section
    if section == 'overview':
        sponsorship_requests = SponsorshipRequest.objects.filter(user=user).order_by('-created_at')
        context['sponsorship_requests'] = sponsorship_requests

        # Handle sponsorship request form submission
        if request.method == 'POST':
            form = SponsorshipRequestForm(request.POST, request.FILES)
            form.user = request.user

            if form.is_valid():
                sponsorship_request = form.save(commit=False)
                sponsorship_request.user = request.user
                sponsorship_request.save()

                # Send email notifications
                try:
                    send_sponsorship_confirmation_email(sponsorship_request)
                    send_sponsorship_admin_notification(sponsorship_request)

                    messages.success(
                        request,
                        'Your sponsorship request has been submitted successfully! '
                        'You will receive a confirmation email shortly, and our team will review your request.'
                    )
                except Exception as e:
                    messages.warning(
                        request,
                        'Your sponsorship request was submitted, but there was an issue sending the confirmation email. '
                        'Our team will still review your request.'
                    )

                return redirect('profile')
            else:
                messages.error(request, 'Please correct the errors below and try again.')
        else:
            form = SponsorshipRequestForm()

        context['sponsorship_form'] = form

    # LMS stats for overview display
    context['lms_stats'] = {
        'total_enrollments': context['total_enrollments'],
        'active_courses': context['active_courses'],
        'completed_courses': context['completed_courses'],
        'total_achievements': context.get('total_achievements', 0),
        'total_learning_hours': context.get('total_learning_hours', 0),
    }

    # Recent enrollments for overview
    context['recent_enrollments'] = enrollments.order_by('-enrollment_date')[:3]

    return render(request, 'registration/unified_profile.html', context)


def calculate_learning_streak(recent_activity):
    """Calculate consecutive days of learning activity"""
    if not recent_activity.exists():
        return 0

    from datetime import date, timedelta
    today = date.today()
    streak = 0
    current_date = today

    # Group activities by date
    activity_dates = set()
    for activity in recent_activity:
        activity_dates.add(activity.completed_at.date())

    # Count consecutive days backwards from today
    while current_date in activity_dates:
        streak += 1
        current_date -= timedelta(days=1)

    return streak


def get_payment_history(user):
    """Get user's payment history"""
    payment_history = []
    if hasattr(user, 'profile') and user.profile.payment_confirmed_at:
        payment_history.append({
            'date': user.profile.payment_confirmed_at,
            'amount': user.profile.payment_amount or 0,
            'method': user.profile.get_payment_method_display() if user.profile.payment_method else 'N/A',
            'reference': user.profile.payment_reference or 'N/A',
            'status': 'Confirmed'
        })
    return payment_history


def get_recent_activity(user):
    """Get user's recent learning activity"""
    from progress.models import LessonProgress
    recent_progress = LessonProgress.objects.filter(
        enrollment__student=user
    ).select_related('lesson', 'enrollment__course').order_by('-completed_at')[:10]

    activities = []
    for progress in recent_progress:
        if progress.completed_at:
            activities.append({
                'type': 'lesson_completed',
                'title': f"Completed: {progress.lesson.title}",
                'course': progress.enrollment.course.title,
                'date': progress.completed_at,
                'icon': 'fas fa-check-circle',
                'color': 'success'
            })
        elif progress.started_at:
            activities.append({
                'type': 'lesson_started',
                'title': f"Started: {progress.lesson.title}",
                'course': progress.enrollment.course.title,
                'date': progress.started_at,
                'icon': 'fas fa-play-circle',
                'color': 'info'
            })

    return activities[:5]  # Return only 5 most recent


# Keep the old profile view for backward compatibility during transition
@login_required
def profile(request):
    """Legacy profile view - redirects to unified profile"""
    return unified_profile(request, section='overview')


def send_sponsorship_emails(sponsorship_request):
    """Send email notifications for sponsorship requests"""
    user = sponsorship_request.user

    # Email to user (confirmation)
    user_subject = 'Sponsorship Request Confirmation - Youth Impact Training Programme'
    user_context = {
        'user': user,
        'sponsorship_request': sponsorship_request,
    }

    user_html_content = render_to_string('emails/sponsorship_confirmation.html', user_context)
    user_text_content = render_to_string('emails/sponsorship_confirmation.txt', user_context)

    user_email = EmailMultiAlternatives(
        subject=user_subject,
        body=user_text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    user_email.attach_alternative(user_html_content, "text/html")
    user_email.send()

    # Email to admin (notification)
    admin_subject = f'New Sponsorship Request - {user.get_full_name() or user.username}'
    admin_context = {
        'user': user,
        'sponsorship_request': sponsorship_request,
    }

    admin_html_content = render_to_string('emails/sponsorship_admin_notification.html', admin_context)
    admin_text_content = render_to_string('emails/sponsorship_admin_notification.txt', admin_context)

    admin_email = EmailMultiAlternatives(
        subject=admin_subject,
        body=admin_text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.ADMIN_EMAIL],
        reply_to=[user.email],
    )
    admin_email.attach_alternative(admin_html_content, "text/html")

    # Attach supporting document if provided
    if sponsorship_request.supporting_document:
        admin_email.attach_file(sponsorship_request.supporting_document.path)

    admin_email.send()

@login_required
def test_email_delivery(request):
    """
    Test email delivery functionality
    Only accessible to logged-in users for security
    """
    if request.method == 'POST':
        test_email = request.POST.get('test_email', request.user.email)

        try:
            # Send test email
            subject = "YITP Email Delivery Test"
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #ff5d15;">🧪 YITP Email Delivery Test</h2>
                    <p>Hello {request.user.first_name or request.user.username},</p>
                    <p>This is a test email to verify that the YITP email delivery system is working correctly.</p>

                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #1a2e53; margin-top: 0;">Test Details:</h3>
                        <ul>
                            <li><strong>Sent by:</strong> {request.user.username} ({request.user.email})</li>
                            <li><strong>Test email:</strong> {test_email}</li>
                            <li><strong>Timestamp:</strong> {timezone.now()}</li>
                        </ul>
                    </div>

                    <p style="color: #28a745; font-weight: bold;">
                        ✅ If you receive this email, the delivery system is working!
                    </p>

                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        Youth Impact Training Programme - Email Delivery Test
                    </p>
                </div>
            </body>
            </html>
            """

            result = send_html_email(
                subject=subject,
                html_content=html_content,
                recipient_list=[test_email]
            )

            if result:
                messages.success(request, f'✅ Test email sent successfully to {test_email}! Please check the inbox (and spam folder).')
            else:
                messages.error(request, f'❌ Failed to send test email to {test_email}. Check the server logs for details.')

        except Exception as e:
            messages.error(request, f'❌ Email test failed: {str(e)}')

    return render(request, 'users/test_email.html')