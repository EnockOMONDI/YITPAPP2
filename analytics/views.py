"""
Analytics Views for YITP Payment Dashboard
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Q
from datetime import datetime, timedelta
import json

from .services import PaymentAnalyticsService
from .models import PaymentAnalytics, UserPaymentBehavior, CourseRevenueAnalytics
from payments.models import Payment
from users.models import Profile


@method_decorator(staff_member_required, name='dispatch')
class AnalyticsDashboardView(TemplateView):
    """Main analytics dashboard view"""
    template_name = 'analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get dashboard summary
        context['summary'] = PaymentAnalyticsService.get_dashboard_summary()
        
        # Get payment method performance
        context['payment_methods'] = PaymentAnalyticsService.get_payment_method_performance()
        
        # Get installment analytics
        context['installments'] = PaymentAnalyticsService.get_installment_analytics()
        
        # Get recent analytics records
        context['recent_analytics'] = PaymentAnalytics.objects.all()[:7]
        
        return context


@staff_member_required
def revenue_trends_api(request):
    """API endpoint for revenue trends data"""
    days = int(request.GET.get('days', 30))
    trends = PaymentAnalyticsService.get_revenue_trends(days)
    return JsonResponse(trends)


@staff_member_required
def payment_method_performance_api(request):
    """API endpoint for payment method performance data"""
    performance = PaymentAnalyticsService.get_payment_method_performance()
    return JsonResponse(performance)


@staff_member_required
def installment_analytics_api(request):
    """API endpoint for installment analytics data"""
    analytics = PaymentAnalyticsService.get_installment_analytics()
    return JsonResponse(analytics)


@staff_member_required
def user_behavior_analytics_api(request):
    """API endpoint for user behavior analytics"""
    
    # Top users by payment amount
    top_users = UserPaymentBehavior.objects.filter(
        total_amount_paid__gt=0
    ).order_by('-total_amount_paid')[:10]
    
    # Payment method preferences
    method_preferences = UserPaymentBehavior.objects.exclude(
        preferred_payment_method=''
    ).values('preferred_payment_method').annotate(
        count=Count('id')
    )
    
    # Risk analysis
    high_risk_users = UserPaymentBehavior.objects.filter(
        payment_failure_rate__gt=50
    ).count()
    
    return JsonResponse({
        'top_users': [
            {
                'username': user.user.username,
                'email': user.user.email,
                'total_paid': float(user.total_amount_paid),
                'payment_count': user.successful_payments,
                'preferred_method': user.preferred_payment_method,
            }
            for user in top_users
        ],
        'method_preferences': list(method_preferences),
        'high_risk_users': high_risk_users,
        'total_users_with_payments': UserPaymentBehavior.objects.count(),
    })


@staff_member_required
def course_revenue_analytics_api(request):
    """API endpoint for course revenue analytics"""
    
    # Top courses by revenue
    top_courses = CourseRevenueAnalytics.objects.filter(
        total_revenue__gt=0
    ).order_by('-total_revenue')[:10]
    
    # Course conversion rates
    conversion_data = CourseRevenueAnalytics.objects.filter(
        total_enrollments__gt=0
    ).order_by('-conversion_rate')[:10]
    
    return JsonResponse({
        'top_courses': [
            {
                'title': course.course.title,
                'total_revenue': float(course.total_revenue),
                'paid_enrollments': course.paid_enrollments,
                'total_enrollments': course.total_enrollments,
                'conversion_rate': float(course.conversion_rate),
                'installment_completion_rate': float(course.installment_completion_rate),
            }
            for course in top_courses
        ],
        'conversion_rates': [
            {
                'title': course.course.title,
                'conversion_rate': float(course.conversion_rate),
                'total_enrollments': course.total_enrollments,
                'paid_enrollments': course.paid_enrollments,
            }
            for course in conversion_data
        ],
    })


@method_decorator(staff_member_required, name='dispatch')
class PaymentMethodAnalyticsView(TemplateView):
    """Detailed payment method analytics view"""
    template_name = 'analytics/payment_methods.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get detailed payment method performance
        context['performance'] = PaymentAnalyticsService.get_payment_method_performance()
        
        # Get recent payment trends by method
        context['trends'] = PaymentAnalyticsService.get_revenue_trends(30)
        
        return context


@method_decorator(staff_member_required, name='dispatch')
class UserBehaviorAnalyticsView(TemplateView):
    """User behavior analytics view"""
    template_name = 'analytics/user_behavior.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user behavior statistics
        context['total_users'] = UserPaymentBehavior.objects.count()
        context['high_value_users'] = UserPaymentBehavior.objects.filter(
            total_amount_paid__gt=10000
        ).count()
        context['high_risk_users'] = UserPaymentBehavior.objects.filter(
            payment_failure_rate__gt=50
        ).count()
        
        return context


@method_decorator(staff_member_required, name='dispatch')
class CourseRevenueAnalyticsView(TemplateView):
    """Course revenue analytics view"""
    template_name = 'analytics/course_revenue.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get course analytics summary
        context['total_courses'] = CourseRevenueAnalytics.objects.count()
        context['total_revenue'] = CourseRevenueAnalytics.objects.aggregate(
            total=Sum('total_revenue')
        )['total'] or 0
        
        return context


@staff_member_required
def generate_analytics_report(request):
    """Generate analytics report for a specific date range"""
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Start date and end date are required'}, status=400)
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    
    # Generate analytics for the date range
    analytics = PaymentAnalytics.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Aggregate data
    total_revenue = sum(a.total_revenue for a in analytics)
    total_payments = sum(a.total_payments for a in analytics)
    avg_daily_revenue = total_revenue / len(analytics) if analytics else 0
    
    # Payment method breakdown
    method_breakdown = {
        'mpesa': {
            'payments': sum(a.mpesa_payments for a in analytics),
            'revenue': sum(a.mpesa_revenue for a in analytics),
        },
        'bank_transfer': {
            'payments': sum(a.bank_transfer_payments for a in analytics),
            'revenue': sum(a.bank_transfer_revenue for a in analytics),
        },
        'paypal': {
            'payments': sum(a.paypal_payments for a in analytics),
            'revenue': sum(a.paypal_revenue for a in analytics),
        },
    }
    
    return JsonResponse({
        'date_range': {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'days': len(analytics),
        },
        'summary': {
            'total_revenue': float(total_revenue),
            'total_payments': total_payments,
            'avg_daily_revenue': float(avg_daily_revenue),
        },
        'method_breakdown': {
            method: {
                'payments': data['payments'],
                'revenue': float(data['revenue']),
            }
            for method, data in method_breakdown.items()
        },
        'daily_data': [
            {
                'date': a.date.strftime('%Y-%m-%d'),
                'revenue': float(a.total_revenue),
                'payments': a.total_payments,
                'confirmed': a.confirmed_payments,
                'pending': a.pending_payments,
            }
            for a in analytics
        ],
    })
