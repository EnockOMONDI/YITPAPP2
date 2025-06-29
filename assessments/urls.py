from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    # Quiz URLs
    path('', views.AssessmentDashboardView.as_view(), name='assessment_dashboard'),
    path('quizzes/', views.QuizListView.as_view(), name='quiz_list'),
    path('quizzes/<int:quiz_id>/', views.QuizDetailView.as_view(), name='quiz_detail'),
    path('quizzes/<int:quiz_id>/take/', views.TakeQuizView.as_view(), name='take_quiz'),
    path('quiz-results/<int:attempt_id>/', views.QuizResultsView.as_view(), name='quiz_results'),

    # Assignment URLs
    path('assignments/', views.AssignmentListView.as_view(), name='assignment_list'),
    path('assignments/<int:assignment_id>/', views.AssignmentDetailView.as_view(), name='assignment_detail'),
    path('assignments/<int:assignment_id>/submit/', views.SubmitAssignmentView.as_view(), name='submit_assignment'),
]
