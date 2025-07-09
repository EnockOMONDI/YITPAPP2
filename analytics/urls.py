"""
URL Configuration for Analytics App
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard views
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('payment-methods/', views.PaymentMethodAnalyticsView.as_view(), name='payment_methods'),
    path('user-behavior/', views.UserBehaviorAnalyticsView.as_view(), name='user_behavior'),
    path('course-revenue/', views.CourseRevenueAnalyticsView.as_view(), name='course_revenue'),
    
    # API endpoints
    path('api/revenue-trends/', views.revenue_trends_api, name='revenue_trends_api'),
    path('api/payment-methods/', views.payment_method_performance_api, name='payment_method_performance_api'),
    path('api/installments/', views.installment_analytics_api, name='installment_analytics_api'),
    path('api/user-behavior/', views.user_behavior_analytics_api, name='user_behavior_analytics_api'),
    path('api/course-revenue/', views.course_revenue_analytics_api, name='course_revenue_analytics_api'),
    path('api/generate-report/', views.generate_analytics_report, name='generate_analytics_report'),
]
