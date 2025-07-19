from django.urls import path
from . import views

app_name = 'course_builder'

urlpatterns = [
    # Main course builder dashboard
    path('', views.CourseBuilderDashboardView.as_view(), name='dashboard'),
    
    # Course creation wizard
    path('wizard/', views.CourseBuilderWizardView.as_view(), name='wizard'),
    path('wizard/step/<int:step>/', views.CourseBuilderWizardView.as_view(), name='wizard_step'),
    
    # API endpoints for AJAX operations
    path('api/', views.CourseBuilderAPIView.as_view(), name='api'),

    # Media management
    path('media/', views.MediaLibraryView.as_view(), name='media_library'),
    path('media/upload/', views.MediaUploadView.as_view(), name='upload_media'),

    # Content templates
    path('templates/', views.ContentTemplateView.as_view(), name='content_templates'),

    # Template selection
    path('template/<int:template_id>/', views.CourseBuilderWizardView.as_view(), name='from_template'),
]
