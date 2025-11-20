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


SUPPORT_FAQS = [
    {
        "question": "How long does the Youth Impact Training Programme take?",
        "answer": (
            "The core programme runs for 10 weeks with a mix of live"
            " sessions, self-paced coursework, and mentorship. Learners can"
            " continue exploring optional mastery sprints even after they finish."
        ),
    },
    {
        "question": "Where can I see my course progress and certificates?",
        "answer": (
            "Log into your profile at /profile/ and open the My Courses or"
            " Analytics tabs. From there you can download certificates, track"
            " progress, and jump back into the last lesson you viewed."
        ),
    },
    {
        "question": "How do I get help with payments or sponsorship applications?",
        "answer": (
            "Send us an email at info@youthimpactglobal.com or WhatsApp"
            " +254722646959 with your payment reference. Our finance desk"
            " typically replies within one business day."
        ),
    },
    {
        "question": "Can instructors or partners access a dedicated dashboard?",
        "answer": (
            "Yes. Approved instructors and project partners receive their own"
            " dashboards with course management tools. Reach out to our team"
            " if you need your instructor profile activated."
        ),
    },
]

def _get_resume_destination(user):
    """
    Determine the best resume destination for a returning learner.
    Returns the last active lesson URL when available, otherwise dashboard.
    """
    # Role-specific destinations first
    if getattr(user, 'is_superuser', False):
        return reverse('users:superuser_dashboard')

    if hasattr(user, 'instructor_profile'):
        try:
            profile = user.instructor_profile
            if profile and profile.is_active:
                return reverse('users:instructor_profile')
        except Exception:
            pass

    try:
        from django.db.models.functions import Coalesce
        from progress.models import Enrollment, LessonProgress
    except Exception:
        # If related apps are unavailable, skip smart routing
        return None

    enrollments = Enrollment.objects.filter(student=user)
    if not enrollments.exists():
        return reverse('profile')

    last_progress = (
        LessonProgress.objects
        .filter(enrollment__student=user)
        .annotate(last_activity=Coalesce('completed_at', 'started_at'))
        .filter(last_activity__isnull=False)
        .select_related('enrollment__course', 'lesson')
        .order_by('-last_activity')
        .first()
    )

    if last_progress:
        try:
            return reverse(
                'courses:lesson_detail',
                kwargs={
                    'course_slug': last_progress.enrollment.course.slug,
                    'lesson_id': last_progress.lesson.id
                }
            )
        except Exception:
            # If reverse fails for any reason, default to dashboard
            pass

    return reverse('profile')


def home(request):
    """
    Smart home view with intelligent routing based on user authentication status.
    Authenticated users see personalized content, unauthenticated users see marketing content.
    """
    if request.user.is_authenticated:
        resume_url = _get_resume_destination(request.user)
        if resume_url:
            return redirect(resume_url)

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

    context = {
        'support_faqs': SUPPORT_FAQS,
    }

    return render(request, 'yitp/contact.html', context)


def support(request):
    support_channels = [
        {
            "label": "WhatsApp & Phone",
            "value": "+254 722 646 959",
            "href": "https://wa.me/254722646959",
            "icon": "fas fa-mobile-alt",
            "subtext": "Weekdays 9:00am - 6:00pm EAT",
            "new_tab": True,
        },
        {
            "label": "Email",
            "value": "info@youthimpactglobal.com",
            "href": "mailto:info@youthimpactglobal.com",
            "icon": "fas fa-envelope-open-text",
            "subtext": "We respond within 1 business day",
            "new_tab": True,
        },
        {
            "label": "Support Desk",
            "value": "Submit a ticket",
            "href": reverse('yitp:contact'),
            "icon": "fas fa-headset",
            "subtext": "Use the contact form for escalations",
            "new_tab": False,
        },
    ]

    context = {
        'support_channels': support_channels,
        'support_faqs': SUPPORT_FAQS,
    }

    return render(request, 'yitp/support.html', context)


def privacy_policy(request):
    return render(request, 'yitp/privacy_policy.html')


def terms_of_service(request):
    return render(request, 'yitp/terms_of_service.html')


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
