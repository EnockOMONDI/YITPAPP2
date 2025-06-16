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
from . models import Editpage,SecondSection,SecondSectionIcon,SecondSectionBox, SponsorshipRequest, Profile
from .forms import SponsorshipRequestForm
from .otp_views import send_otp_for_registration
from .email_utils import send_login_notification, send_sponsorship_confirmation_email, send_sponsorship_admin_notification

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
def profile(request):
    """User profile view with sponsorship request functionality"""
    # Get user's sponsorship requests
    sponsorship_requests = SponsorshipRequest.objects.filter(user=request.user).order_by('-created_at')

    # Handle sponsorship request form submission
    if request.method == 'POST':
        form = SponsorshipRequestForm(request.POST, request.FILES)
        form.user = request.user  # Set user for validation

        if form.is_valid():
            sponsorship_request = form.save(commit=False)
            sponsorship_request.user = request.user
            sponsorship_request.save()

            # Send email notifications
            try:
                # Send confirmation email to user
                send_sponsorship_confirmation_email(sponsorship_request)
                # Send notification email to admin
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

    return render(request, 'registration/profile.html', {
        'user': request.user,
        'sponsorship_requests': sponsorship_requests,
        'sponsorship_form': form,
    })


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