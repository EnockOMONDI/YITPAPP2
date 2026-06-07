from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import instructor_views
from . import auth_views
from . import content_management
from .magic_link_views import magic_login_view, magic_link_status_view, validate_magic_link_api, magic_link_help_view


app_name = 'users'

urlpatterns = [
    # Redirect legacy marketing URLs to the modern yitp app versions
    path('', RedirectView.as_view(url='/', permanent=True), name='home'),
    path('aboutus/', RedirectView.as_view(url='/about/', permanent=True), name='aboutus'),
    path('programs/', RedirectView.as_view(url='/web_courses_list/', permanent=True), name='programs'),
    path('ourteam/', RedirectView.as_view(url='/team/', permanent=True), name='ourteam'),
    path('contactus/', RedirectView.as_view(url='/contact/', permanent=True), name='contactus'),
    path('test-email/', views.test_email_delivery, name='test_email'),

    # Enhanced Authentication URLs
    path('instructor/profile/', auth_views.InstructorProfileView.as_view(), name='instructor_profile'),
    path('onboarding/', auth_views.instructor_onboarding_check, name='instructor_onboarding'),

    # Instructor Dashboard URLs
    path('instructor/', instructor_views.InstructorDashboardView.as_view(), name='instructor_dashboard'),
    path('instructor/courses/', instructor_views.InstructorCoursesView.as_view(), name='instructor_courses'),
    path('instructor/students/', instructor_views.InstructorStudentsView.as_view(), name='instructor_students'),
    path('instructor/student/<int:student_id>/', instructor_views.InstructorStudentDetailView.as_view(), name='instructor_student_detail'),
    path('instructor/student/<int:student_id>/send-message/', instructor_views.send_message_to_student, name='instructor_send_message'),
    path('instructor/analytics/', instructor_views.InstructorAnalyticsView.as_view(), name='instructor_analytics'),
    path('instructor/messages/', instructor_views.InstructorMessagesView.as_view(), name='instructor_messages'),
    path('instructor/course/<int:course_id>/', instructor_views.instructor_course_detail, name='instructor_course_detail'),
    path('instructor/tutorial/', instructor_views.InstructorTutorialView.as_view(), name='instructor_tutorial'),
    path('instructor/module/<int:module_id>/edit/', instructor_views.EditModuleView.as_view(), name='instructor_edit_module'),
    path('instructor/module/<int:module_id>/lesson/create/', instructor_views.create_module_lesson, name='instructor_create_module_lesson'),
    path('instructor/lesson/<int:lesson_id>/form/', instructor_views.get_lesson_form, name='instructor_get_lesson_form'),
    path('instructor/module/<int:module_id>/quizzes/', instructor_views.ManageModuleQuizzesView.as_view(), name='instructor_manage_quizzes'),
    path('instructor/lesson/<int:lesson_id>/quizzes-list/', instructor_views.get_lesson_quizzes_list, name='instructor_get_lesson_quizzes_list'),
    path('instructor/module/<int:module_id>/quiz/create/', instructor_views.create_module_quiz, name='instructor_create_module_quiz'),
    path('instructor/quiz/<int:quiz_id>/details/', instructor_views.get_quiz_details, name='instructor_get_quiz_details'),
    path('instructor/quiz/add/', instructor_views.AddQuizView.as_view(), name='instructor_add_quiz'),
    path('instructor/quiz/<int:quiz_id>/questions/', instructor_views.EditQuizQuestionsView.as_view(), name='instructor_edit_quiz_questions'),
    path('instructor/quiz/question/<int:question_id>/delete/', instructor_views.delete_quiz_question, name='instructor_delete_quiz_question'),
    path('accountant/dashboard/', instructor_views.AccountantDashboardView.as_view(), name='accountant_dashboard'),
    path('content-manager/dashboard/', instructor_views.ContentManagerDashboardView.as_view(), name='content_manager_dashboard'),

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
    path('superuser/create-user/', views.superuser_create_user, name='superuser_create_user'),

]
