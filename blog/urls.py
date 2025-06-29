"""blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from graphene_django.views import GraphQLView
from django.contrib.auth import views as auth_views

from users import views as user_views
from users.otp_views import verify_otp_view, resend_otp_view, otp_status_view

urlpatterns = [
    path('jet/', include('jet.urls', 'jet')),  # Django Jet URLS
    path('admin/', admin.site.urls),
    path('graphql/', GraphQLView.as_view(graphiql=True)),

    # Custom authentication views
    path('register/', user_views.register, name='register'),
    path('login/', user_views.login, name='login'),
    path('logout/', user_views.logout, name='logout'),

    # Unified profile system with section-based navigation
    path('profile/', user_views.unified_profile, name='profile'),
    path('profile/lms/', user_views.unified_profile, {'section': 'lms'}, name='profile_lms'),
    path('profile/courses/', user_views.unified_profile, {'section': 'courses'}, name='profile_courses'),
    path('profile/analytics/', user_views.unified_profile, {'section': 'analytics'}, name='profile_analytics'),
    path('profile/billing/', user_views.unified_profile, {'section': 'billing'}, name='profile_billing'),

    # OTP verification views
    path('verify-otp/', verify_otp_view, name='verify_otp'),
    path('resend-otp/', resend_otp_view, name='resend_otp'),
    path('otp-status/', otp_status_view, name='otp_status'),

    # Django built-in authentication views (as backup)
    path('accounts/login/', auth_views.LoginView.as_view(), name='django_login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='django_logout'),

    # Password reset functionality
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # Main app URLs
    path('', include('yitp.urls')),
    path('users', include('users.urls')),
    path('blogs/', include('blogapp.urls')),
    path('events/', include('events.urls')),
     # LMS apps
    path('lms/courses/', include('courses.urls')),
    path('lms/progress/', include('progress.urls')),
    path('lms/assessments/', include('assessments.urls')),
    path('lms/communication/', include('communication.urls')),
    path('lms/content/', include('content.urls')),

]

urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)

