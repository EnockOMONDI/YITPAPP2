from django.urls import path
from blogapp import views
from . import views
from . import instructor_views
from . import auth_views
from . import content_management


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

]

