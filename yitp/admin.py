from django.contrib import admin
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User


def dashboard_callback(request, context):
    """
    Dashboard callback for Django Unfold admin interface
    Provides YITP-specific dashboard statistics and information
    """
    try:
        # Get current date for time-based queries
        now = timezone.now()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)

        # User statistics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        staff_users = User.objects.filter(is_staff=True).count()
        new_users_30_days = User.objects.filter(date_joined__gte=last_30_days).count()

        # Course statistics (if courses app is available)
        course_stats = {}
        try:
            from courses.models import Course, Enrollment
            total_courses = Course.objects.count()
            active_courses = Course.objects.filter(is_active=True).count()
            total_enrollments = Enrollment.objects.count()
            recent_enrollments = Enrollment.objects.filter(enrolled_at__gte=last_7_days).count()

            course_stats = {
                'total_courses': total_courses,
                'active_courses': active_courses,
                'total_enrollments': total_enrollments,
                'recent_enrollments': recent_enrollments,
            }
        except ImportError:
            course_stats = {
                'total_courses': 0,
                'active_courses': 0,
                'total_enrollments': 0,
                'recent_enrollments': 0,
            }

        # Blog statistics (if blogapp is available)
        blog_stats = {}
        try:
            from blogapp.models import Post
            total_posts = Post.objects.count()
            published_posts = Post.objects.filter(status='published').count()
            draft_posts = Post.objects.filter(status='draft').count()
            featured_posts = Post.objects.filter(featured=True).count()

            blog_stats = {
                'total_posts': total_posts,
                'published_posts': published_posts,
                'draft_posts': draft_posts,
                'featured_posts': featured_posts,
            }
        except ImportError:
            blog_stats = {
                'total_posts': 0,
                'published_posts': 0,
                'draft_posts': 0,
                'featured_posts': 0,
            }

        # Payment statistics (if payments app is available)
        payment_stats = {}
        try:
            from payments.models import Payment
            total_payments = Payment.objects.count()
            confirmed_payments = Payment.objects.filter(status='confirmed').count()
            pending_payments = Payment.objects.filter(status='pending').count()
            recent_payments = Payment.objects.filter(created_at__gte=last_7_days).count()

            payment_stats = {
                'total_payments': total_payments,
                'confirmed_payments': confirmed_payments,
                'pending_payments': pending_payments,
                'recent_payments': recent_payments,
            }
        except ImportError:
            payment_stats = {
                'total_payments': 0,
                'confirmed_payments': 0,
                'pending_payments': 0,
                'recent_payments': 0,
            }

        # System information
        system_info = {
            'django_version': '5.0.14',
            'environment': 'Development' if hasattr(context, 'DEBUG') and context.get('DEBUG') else 'Production',
            'last_updated': now.strftime('%Y-%m-%d %H:%M:%S'),
        }

        # Dashboard data structure for Unfold
        dashboard_data = [
            {
                'title': 'User Management',
                'description': 'Overview of user accounts and registrations',
                'icon': 'people',
                'color': 'primary',
                'stats': [
                    {'label': 'Total Users', 'value': total_users, 'icon': 'person'},
                    {'label': 'Active Users', 'value': active_users, 'icon': 'person_check'},
                    {'label': 'Staff Users', 'value': staff_users, 'icon': 'admin_panel_settings'},
                    {'label': 'New Users (30 days)', 'value': new_users_30_days, 'icon': 'person_add'},
                ]
            },
            {
                'title': 'Course Management',
                'description': 'Course and enrollment statistics',
                'icon': 'school',
                'color': 'success',
                'stats': [
                    {'label': 'Total Courses', 'value': course_stats['total_courses'], 'icon': 'book'},
                    {'label': 'Active Courses', 'value': course_stats['active_courses'], 'icon': 'play_circle'},
                    {'label': 'Total Enrollments', 'value': course_stats['total_enrollments'], 'icon': 'how_to_reg'},
                    {'label': 'Recent Enrollments', 'value': course_stats['recent_enrollments'], 'icon': 'trending_up'},
                ]
            },
            {
                'title': 'Blog Management',
                'description': 'Blog posts and content statistics',
                'icon': 'article',
                'color': 'info',
                'stats': [
                    {'label': 'Total Posts', 'value': blog_stats['total_posts'], 'icon': 'article'},
                    {'label': 'Published Posts', 'value': blog_stats['published_posts'], 'icon': 'publish'},
                    {'label': 'Draft Posts', 'value': blog_stats['draft_posts'], 'icon': 'draft'},
                    {'label': 'Featured Posts', 'value': blog_stats['featured_posts'], 'icon': 'star'},
                ]
            },
            {
                'title': 'Payment Management',
                'description': 'Payment processing and transaction overview',
                'icon': 'payment',
                'color': 'warning',
                'stats': [
                    {'label': 'Total Payments', 'value': payment_stats['total_payments'], 'icon': 'payment'},
                    {'label': 'Confirmed Payments', 'value': payment_stats['confirmed_payments'], 'icon': 'check_circle'},
                    {'label': 'Pending Payments', 'value': payment_stats['pending_payments'], 'icon': 'pending'},
                    {'label': 'Recent Payments', 'value': payment_stats['recent_payments'], 'icon': 'schedule'},
                ]
            },
        ]

        # Add dashboard data to context
        context.update({
            'yitp_dashboard_data': dashboard_data,
            'yitp_system_info': system_info,
            'yitp_quick_actions': [
                {'title': 'Add New User', 'url': '/admin/auth/user/add/', 'icon': 'person_add'},
                {'title': 'Create Course', 'url': '/admin/courses/course/add/', 'icon': 'add_circle'},
                {'title': 'Write Blog Post', 'url': '/admin/blogapp/post/add/', 'icon': 'edit'},
                {'title': 'View Payments', 'url': '/admin/payments/payment/', 'icon': 'payment'},
            ]
        })

    except Exception as e:
        # Fallback in case of any errors
        context.update({
            'yitp_dashboard_error': f'Dashboard data unavailable: {str(e)}',
            'yitp_system_info': {
                'django_version': '5.0.14',
                'environment': 'Unknown',
                'last_updated': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
        })

    return context


# Register your models here.
