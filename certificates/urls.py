from django.urls import path
from . import views

app_name = 'certificates'

urlpatterns = [
    # Public certificate verification (no login required)
    path('verify/<str:verification_code>/', views.CertificateVerificationView.as_view(), name='verify'),
    
    # Authenticated certificate access
    path('download/<str:verification_code>/', views.CertificateDownloadView.as_view(), name='download'),
    path('my-certificates/', views.MyCertificatesView.as_view(), name='my_certificates'),
    path('detail/<str:verification_code>/', views.CertificateDetailView.as_view(), name='detail'),
]
