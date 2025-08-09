from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods


def home(request):
    """
    Smart home view with intelligent routing based on user authentication status.
    Authenticated users see personalized content, unauthenticated users see marketing content.
    """
    context = {}

    if request.user.is_authenticated:
        # Add personalized context for authenticated users
        context.update({
            'user_authenticated': True,
            'show_dashboard_link': True,
            'show_course_progress': True,
        })
    else:
        # Add marketing context for unauthenticated users
        context.update({
            'user_authenticated': False,
            'show_registration_cta': True,
            'show_course_overview': True,
        })

    return render(request, 'yitp/index.html', context)

def web_courses_list(request):
    """
    Unified course discovery view that adapts based on user authentication status.
    For authenticated users: redirects to LMS course listing
    For unauthenticated users: shows static course overview
    """
    if request.user.is_authenticated:
        # Redirect authenticated users to the LMS course listing
        from django.shortcuts import redirect
        return redirect('courses:course_list')

    # Show static course overview for unauthenticated users
    return render(request, 'yitp/web_courses_list.html')

def documentation(request):
    """
    YITP User Flow Documentation page
    Provides comprehensive technical documentation and visual guides
    for understanding YITP user workflows and system processes.
    """
    return render(request, 'yitp/documentation.html')

def about(request):
    
    return render(request, 'yitp/about.html')

def team(request):
    
    return render(request, 'yitp/ourteam.html')

def registration_redirect(request):
    """
    Smart redirect for legacy registration URL.
    Redirects to the canonical registration experience.
    """
    from django.shortcuts import redirect
    return redirect('register')

def registration(request):
    """
    Legacy registration view - redirects to canonical registration
    """
    from django.shortcuts import redirect
    return redirect('register')

# registration2 view removed - all registration now handled by canonical 'register' URL

@login_required
def welcome(request):
    """
    Welcome page for newly registered and verified users
    Shows next steps and course enrollment options with smart navigation
    """
    # Check if user has already enrolled in courses
    from progress.models import Enrollment
    from users.models import Profile

    user_enrollments = Enrollment.objects.filter(student=request.user)

    # Get user profile (should exist from OTP verification)
    try:
        profile = request.user.profile
        # Update completion percentage in case profile was modified
        profile.update_profile_completion()
    except Profile.DoesNotExist:
        # Fallback: create profile if somehow missing (shouldn't happen after OTP verification)
        profile = Profile.objects.create(user=request.user)
        profile.update_profile_completion()

    # Check if user just completed OTP verification (for onboarding logic)
    just_completed_otp = request.session.get('just_completed_otp_verification', False)
    otp_verification_timestamp = request.session.get('otp_verification_timestamp')

    context = {
        'user': request.user,
        'show_course_enrollment': True,
        'has_enrollments': user_enrollments.exists(),
        'enrollment_count': user_enrollments.count(),
        'just_completed_otp': just_completed_otp,
        'otp_verification_timestamp': otp_verification_timestamp,
        'next_steps': [
            'Complete your profile information',
            'Browse available courses',
            'Enroll in your first course',
            'Start your learning journey'
        ],
        'smart_navigation': {
            'dashboard_url': '/lms/dashboard/',
            'courses_url': '/lms/courses/',
            'profile_url': '/profile/',
        }
    }
    return render(request, 'yitp/welcome.html', context)

def events(request):
    
    return render(request, 'yitp/events.html')

def faqs(request):
    
    return render(request, 'yitp/faqs.html')

def contact(request):
    # Add a test message to verify messages framework is working
    if request.method == 'GET':
        messages.info(request, 'Welcome to our contact page! Feel free to reach out to us.')

    return render(request, 'yitp/contact.html')


def translation_demo(request):
    """Demo page to showcase the YITP translation system"""
    return render(request, 'yitp/translation_demo.html')


def translation_test(request):
    """Test page to debug and verify the YITP translation system"""
    return render(request, 'yitp/translation_test.html')


def coursedetail1(request):
    
    return render(request, 'yitp/coursedetail1.html')   

def coursedetail2(request):
    
    return render(request, 'yitp/coursedetail2.html')

def coursedetail3(request):
    
    return render(request, 'yitp/coursedetail3.html')  

def coursedetail4(request):
    
    return render(request, 'yitp/coursedetail4.html')      

def coursedetail5(request):
    
    return render(request, 'yitp/coursedetail5.html')

def coursedetail6(request):

    return render(request, 'yitp/coursedetail6.html')


@cache_page(60 * 60 * 24)  # Cache for 24 hours
@require_http_methods(["GET"])
def sitemap_xml(request):
    """
    Generate XML sitemap for SEO optimization
    """
    # Define static pages with their priorities and change frequencies
    static_pages = [
        {
            'url': reverse('yitp:home'),
            'priority': '1.0',
            'changefreq': 'daily',
            'lastmod': timezone.now().date()
        },
        {
            'url': reverse('yitp:about'),
            'priority': '0.8',
            'changefreq': 'monthly',
            'lastmod': timezone.now().date()
        },
        {
            'url': reverse('yitp:web_courses_list'),
            'priority': '0.9',
            'changefreq': 'weekly',
            'lastmod': timezone.now().date()
        },
        {
            'url': reverse('yitp:team'),
            'priority': '0.7',
            'changefreq': 'monthly',
            'lastmod': timezone.now().date()
        },
        {
            'url': reverse('yitp:contact'),
            'priority': '0.6',
            'changefreq': 'monthly',
            'lastmod': timezone.now().date()
        },
        {
            'url': reverse('yitp:faqs'),
            'priority': '0.6',
            'changefreq': 'monthly',
            'lastmod': timezone.now().date()
        },
        {
            'url': reverse('yitp:documentation'),
            'priority': '0.5',
            'changefreq': 'monthly',
            'lastmod': timezone.now().date()
        },
        {
            'url': reverse('yitp:events'),
            'priority': '0.7',
            'changefreq': 'weekly',
            'lastmod': timezone.now().date()
        },
    ]

    # Add course detail pages
    for i in range(1, 7):
        static_pages.append({
            'url': reverse(f'yitp:coursedetail{i}'),
            'priority': '0.8',
            'changefreq': 'monthly',
            'lastmod': timezone.now().date()
        })

    # Build absolute URLs
    for page in static_pages:
        page['url'] = request.build_absolute_uri(page['url'])

    # Render sitemap XML
    sitemap_xml = render_to_string('yitp/sitemap.xml', {
        'pages': static_pages,
        'domain': request.get_host(),
    })

    return HttpResponse(sitemap_xml, content_type='application/xml')


@cache_page(60 * 60 * 24)  # Cache for 24 hours
@require_http_methods(["GET"])
def robots_txt(request):
    """
    Generate robots.txt for SEO optimization
    """
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /lms/",
        "Disallow: /users/login/",
        "Disallow: /users/register/",
        "",
        f"Sitemap: {request.build_absolute_uri(reverse('yitp:sitemap'))}",
    ]

    return HttpResponse("\n".join(lines), content_type="text/plain")