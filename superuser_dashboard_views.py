"""
Super Admin Dashboard Views for YITP Project Owner
Custom dashboard with comprehensive analytics and management tools
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
import json
import csv

# Import YITP models
from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import Enrollment, LessonProgress, QuizAttempt
from users.models import Profile
from payments.models import Payment

def is_superuser(user):
    """Check if user is superuser"""
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_superuser)
def superuser_dashboard(request):
    """Main super admin dashboard with comprehensive analytics"""
    
    # Get date ranges
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    current_month_start = today.replace(day=1)
    
    # User Analytics
    total_users = User.objects.count()
    active_users_30d = User.objects.filter(last_login__gte=last_30_days).count()
    new_users_7d = User.objects.filter(date_joined__gte=last_7_days).count()
    new_users_30d = User.objects.filter(date_joined__gte=last_30_days).count()
    
    # Revenue & Payment Metrics
    total_payments = Payment.objects.filter(status='completed').aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    monthly_revenue = Payment.objects.filter(
        status='completed',
        created_at__gte=current_month_start
    ).aggregate(total=Sum('amount'))
    
    pending_payments = Payment.objects.filter(status='pending').count()
    failed_payments = Payment.objects.filter(status='failed').count()
    
    # Course & Content Statistics
    total_courses = Course.objects.count()
    published_courses = Course.objects.filter(is_published=True).count()
    total_modules = Module.objects.count()
    total_lessons = Lesson.objects.count()
    total_quizzes = Quiz.objects.count()
    
    # Enrollment Statistics
    total_enrollments = Enrollment.objects.count()
    active_enrollments = Enrollment.objects.filter(status='active').count()
    completed_enrollments = Enrollment.objects.filter(status='completed').count()
    
    # Course popularity
    popular_courses = Course.objects.annotate(
        enrollment_count=Count('enrollments')
    ).order_by('-enrollment_count')[:5]
    
    # Instructor Management
    instructors = User.objects.filter(courses_taught__isnull=False).distinct()
    total_instructors = instructors.count()
    
    # Recent Activities
    recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')[:10]
    recent_payments = Payment.objects.select_related('user').order_by('-created_at')[:10]
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # Quiz Performance
    avg_quiz_score = QuizAttempt.objects.filter(
        completed_at__isnull=False
    ).aggregate(avg_score=Avg('score'))
    
    # System Health
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "Connected"
        db_status_class = "success"
    except:
        db_status = "Error"
        db_status_class = "danger"
    
    # Daily user registration trend (last 30 days)
    daily_registrations = []
    for i in range(30):
        date = today - timedelta(days=i)
        count = User.objects.filter(date_joined__date=date).count()
        daily_registrations.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    daily_registrations.reverse()
    
    # Monthly revenue trend (last 12 months)
    monthly_revenue_trend = []
    for i in range(12):
        month_start = (today.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        revenue = Payment.objects.filter(
            status='completed',
            created_at__date__gte=month_start,
            created_at__date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_revenue_trend.append({
            'month': month_start.strftime('%Y-%m'),
            'revenue': float(revenue)
        })
    monthly_revenue_trend.reverse()
    
    context = {
        # User Analytics
        'total_users': total_users,
        'active_users_30d': active_users_30d,
        'new_users_7d': new_users_7d,
        'new_users_30d': new_users_30d,
        'daily_registrations': json.dumps(daily_registrations),
        
        # Revenue & Payments
        'total_revenue': total_payments['total'] or 0,
        'total_paid_users': total_payments['count'] or 0,
        'monthly_revenue': monthly_revenue['total'] or 0,
        'pending_payments': pending_payments,
        'failed_payments': failed_payments,
        'monthly_revenue_trend': json.dumps(monthly_revenue_trend),
        
        # Course & Content
        'total_courses': total_courses,
        'published_courses': published_courses,
        'total_modules': total_modules,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
        'popular_courses': popular_courses,
        
        # Enrollments
        'total_enrollments': total_enrollments,
        'active_enrollments': active_enrollments,
        'completed_enrollments': completed_enrollments,
        'completion_rate': round((completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0, 1),
        
        # Instructors
        'total_instructors': total_instructors,
        'instructors': instructors[:10],
        
        # Recent Activities
        'recent_enrollments': recent_enrollments,
        'recent_payments': recent_payments,
        'recent_users': recent_users,
        
        # Performance
        'avg_quiz_score': round(avg_quiz_score['avg_score'] or 0, 1),
        
        # System Health
        'db_status': db_status,
        'db_status_class': db_status_class,
        'current_time': timezone.now(),
    }
    
    return render(request, 'users/superuser_dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def export_users_csv(request):
    """Export users data to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="yitp_users_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Date Joined', 'Last Login', 'Is Active'])
    
    users = User.objects.all().order_by('-date_joined')
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
            'Yes' if user.is_active else 'No'
        ])
    
    return response

@login_required
@user_passes_test(is_superuser)
def export_enrollments_csv(request):
    """Export enrollments data to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="yitp_enrollments_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Student', 'Course', 'Enrollment Date', 'Status', 'Progress %', 'Completion Date'])
    
    enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')
    for enrollment in enrollments:
        writer.writerow([
            enrollment.id,
            enrollment.student.username,
            enrollment.course.title,
            enrollment.enrollment_date.strftime('%Y-%m-%d %H:%M:%S'),
            enrollment.status,
            f"{enrollment.progress_percentage}%",
            enrollment.completion_date.strftime('%Y-%m-%d %H:%M:%S') if enrollment.completion_date else 'Not completed'
        ])
    
    return response

@login_required
@user_passes_test(is_superuser)
def export_payments_csv(request):
    """Export payments data to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="yitp_payments_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Amount', 'Currency', 'Status', 'Payment Method', 'Created At', 'Updated At'])
    
    payments = Payment.objects.select_related('user').order_by('-created_at')
    for payment in payments:
        writer.writerow([
            payment.id,
            payment.user.username if payment.user else 'Anonymous',
            payment.amount,
            payment.currency,
            payment.status,
            payment.payment_method,
            payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            payment.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response

@login_required
@user_passes_test(is_superuser)
def dashboard_api_data(request):
    """API endpoint for real-time dashboard data"""
    data_type = request.GET.get('type', 'overview')
    
    if data_type == 'overview':
        # Real-time overview data
        data = {
            'total_users': User.objects.count(),
            'active_enrollments': Enrollment.objects.filter(status='active').count(),
            'total_revenue': float(Payment.objects.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or 0),
            'pending_payments': Payment.objects.filter(status='pending').count(),
            'timestamp': timezone.now().isoformat()
        }
    elif data_type == 'recent_activity':
        # Recent activity data
        recent_enrollments = Enrollment.objects.select_related('student', 'course').order_by('-enrollment_date')[:5]
        data = {
            'recent_enrollments': [
                {
                    'student': enrollment.student.username,
                    'course': enrollment.course.title,
                    'date': enrollment.enrollment_date.strftime('%Y-%m-%d %H:%M')
                }
                for enrollment in recent_enrollments
            ]
        }
    else:
        data = {'error': 'Invalid data type'}
    
    return JsonResponse(data)
