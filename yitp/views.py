from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from django.contrib.auth.decorators import login_required


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
    Redirects to the unified registration experience.
    """
    from django.shortcuts import redirect
    return redirect('yitp:registration2')

def registration(request):
    """
    Legacy registration view - redirects to unified registration
    """
    from django.shortcuts import redirect
    return redirect('yitp:registration2')

def registration2(request):
    """
    Unified registration view - the primary registration experience
    """
    if request.user.is_authenticated:
        # Redirect authenticated users to their dashboard
        from django.shortcuts import redirect
        return redirect('courses:dashboard')

    return render(request, 'yitp/registration2.html')

@login_required
def welcome(request):
    """
    Welcome page for newly registered and verified users
    Shows next steps and course enrollment options with smart navigation
    """
    # Check if user has already enrolled in courses
    from courses.models import Enrollment
    user_enrollments = Enrollment.objects.filter(student=request.user)

    context = {
        'user': request.user,
        'show_course_enrollment': True,
        'has_enrollments': user_enrollments.exists(),
        'enrollment_count': user_enrollments.count(),
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