from django.urls import path
from blogapp import views
from . import views
from . import instructor_views
from . import auth_views
from . import content_management
from .magic_link_views import magic_login_view, magic_link_status_view, validate_magic_link_api, magic_link_help_view


app_name = 'users'

urlpatterns = [
    path('', views.home, name='home'),
    path('aboutus/', views.aboutus, name='aboutus'),
    path('programs/', views.programs, name='programs'),
    path('ourteam/', views.ourteam, name='ourteam'),
    path('contactus/', views.contactus, name='contactus'),
    path('test-email/', views.test_email_delivery, name='test_email'),

    # Enhanced Authentication URLs
    path('instructor/profile/', auth_views.InstructorProfileView.as_view(), name='instructor_profile'),
    path('onboarding/', auth_views.instructor_onboarding_check, name='instructor_onboarding'),

    # Instructor Dashboard URLs
    path('instructor/', instructor_views.InstructorDashboardView.as_view(), name='instructor_dashboard'),
    path('instructor/courses/', instructor_views.InstructorCoursesView.as_view(), name='instructor_courses'),
    path('instructor/analytics/', instructor_views.InstructorAnalyticsView.as_view(), name='instructor_analytics'),
    path('instructor/messages/', instructor_views.InstructorMessagesView.as_view(), name='instructor_messages'),
    path('instructor/course/<int:course_id>/', instructor_views.instructor_course_detail, name='instructor_course_detail'),
    path('instructor/tutorial/', instructor_views.InstructorTutorialView.as_view(), name='instructor_tutorial'),

    # Content Management URLs
    path('content/', content_management.ContentManagementView.as_view(), name='content_management'),
    path('upload-ajax/', content_management.upload_file_ajax, name='upload_file_ajax'),
    path('bulk-import/', content_management.bulk_import_content, name='bulk_import_content'),
    path('media-library/', content_management.media_library, name='media_library'),

    # Magic Link Authentication URLs
    path('magic-login/<str:token>/', magic_login_view, name='magic_login'),
    path('magic-link-status/', magic_link_status_view, name='magic_link_status'),
    path('api/validate-magic-link/', validate_magic_link_api, name='validate_magic_link_api'),
    path('magic-link-help/', magic_link_help_view, name='magic_link_help'),

    # Timezone Management URLs
    path('set-timezone/', views.set_timezone, name='set_timezone'),
    path('timezone-info/', views.get_timezone_info, name='timezone_info'),

    # Debug URLs (for production troubleshooting)
    path('debug-git/', views.debug_git_info, name='debug_git_info'),

    # Super Admin Dashboard URLs
    path('superuser/profile/', views.superuser_dashboard, name='superuser_dashboard'),
    path('superuser/export/users/', views.export_users_csv, name='export_users_csv'),
    path('superuser/export/enrollments/', views.export_enrollments_csv, name='export_enrollments_csv'),
    path('superuser/export/payments/', views.export_payments_csv, name='export_payments_csv'),
    path('superuser/api/data/', views.dashboard_api_data, name='dashboard_api_data'),

]


# Updated: 2025-09-08T01:13:26.981407