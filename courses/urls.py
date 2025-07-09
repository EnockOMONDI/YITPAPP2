from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'courses'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('how-it-works/', views.HowItWorksView.as_view(), name='how_it_works'),
    path('admin-support/', views.AdminSupportView.as_view(), name='admin_support'),
    path('courses/', views.CourseListView.as_view(), name='course_list'),
    path('courses/<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('courses/<slug:course_slug>/enroll/', views.EnrollView.as_view(), name='enroll'),
    path('courses/<slug:course_slug>/modules/<int:module_id>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/', views.LessonDetailView.as_view(), name='lesson_detail'),
    path('courses/<slug:course_slug>/lessons/<int:lesson_id>/complete/', views.LessonCompleteView.as_view(), name='lesson_complete'),
    path('my-courses/', views.MyCoursesView.as_view(), name='my_courses'),

    # Redirect old LMS profile to unified profile with LMS section
    path('profile/', RedirectView.as_view(pattern_name='profile_lms', permanent=False), name='lms_profile_redirect'),
]

