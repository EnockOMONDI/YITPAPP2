from django.urls import path
from . import views

app_name = 'progress'

urlpatterns = [
    # Progress tracking URLs
    path('', views.ProgressDashboardView.as_view(), name='dashboard'),
    path('my-progress/', views.MyProgressView.as_view(), name='my_progress'),
    path('course/<int:course_id>/progress/', views.CourseProgressView.as_view(), name='course_progress'),
    path('lesson/<int:lesson_id>/progress/', views.LessonProgressView.as_view(), name='lesson_progress'),
    
    # Enrollment URLs
    path('enrollments/', views.EnrollmentListView.as_view(), name='enrollments'),
    path('enroll/<int:course_id>/', views.EnrollView.as_view(), name='enroll'),
    path('unenroll/<int:course_id>/', views.UnenrollView.as_view(), name='unenroll'),
    
    # Achievements and Analytics
    path('achievements/', views.AchievementsView.as_view(), name='achievements'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('learning-paths/', views.LearningPathsView.as_view(), name='learning_paths'),
    path('study-sessions/', views.StudySessionsView.as_view(), name='study_sessions'),
    path('analytics/', views.ProgressAnalyticsView.as_view(), name='analytics'),
    
    # API endpoints for AJAX updates
    path('api/update-lesson-progress/', views.UpdateLessonProgressView.as_view(), name='update_lesson_progress'),
    path('api/start-study-session/', views.StartStudySessionView.as_view(), name='start_study_session'),
    path('api/end-study-session/', views.EndStudySessionView.as_view(), name='end_study_session'),
    path('api/update-study-goals/', views.UpdateStudyGoalsView.as_view(), name='update_study_goals'),
]
