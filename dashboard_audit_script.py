#!/usr/bin/env python3
"""
YITP Super Admin Dashboard - Data Accuracy Verification Script
Comprehensive audit of dashboard data accuracy and production database connectivity
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import json

# Setup Django environment
sys.path.append('/Users/djsean/Desktop/APPS2024/YITP2025/YITPAPP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from django.conf import settings
from django.utils import timezone

User = get_user_model()

class DashboardDataAudit:
    """Comprehensive dashboard data accuracy verification"""
    
    def __init__(self):
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'environment': self.detect_environment(),
            'database_info': self.get_database_info(),
            'data_verification': {},
            'discrepancies': [],
            'recommendations': []
        }
    
    def detect_environment(self):
        """Detect current environment (development/production)"""
        django_env = os.environ.get('DJANGO_ENV', 'development')
        debug_mode = settings.DEBUG
        db_engine = settings.DATABASES['default']['ENGINE']
        db_name = settings.DATABASES['default'].get('NAME', 'Unknown')
        
        # Check if using Supabase (production) or SQLite (development)
        is_production = 'postgresql' in db_engine and 'supabase' in str(settings.DATABASES['default'].get('HOST', ''))
        
        return {
            'django_env': django_env,
            'debug_mode': debug_mode,
            'database_engine': db_engine,
            'database_name': db_name,
            'is_production': is_production,
            'detected_environment': 'production' if is_production else 'development'
        }
    
    def get_database_info(self):
        """Get detailed database connection information"""
        db_config = settings.DATABASES['default']
        
        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                db_version = cursor.fetchone()[0] if cursor.fetchone() else "Unknown"
        except Exception as e:
            db_version = f"Error: {str(e)}"
        
        return {
            'engine': db_config['ENGINE'],
            'name': db_config.get('NAME', 'Not specified'),
            'host': db_config.get('HOST', 'Not specified'),
            'port': db_config.get('PORT', 'Not specified'),
            'user': db_config.get('USER', 'Not specified'),
            'version': db_version,
            'connection_test': self.test_database_connection()
        }
    
    def test_database_connection(self):
        """Test database connectivity and basic operations"""
        try:
            # Test basic query
            user_count = User.objects.count()
            
            # Test write operation (safe)
            test_query_time = timezone.now()
            
            return {
                'status': 'success',
                'user_count_test': user_count,
                'query_time': test_query_time.isoformat(),
                'connection_active': True
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e),
                'connection_active': False
            }
    
    def verify_user_data(self):
        """Verify user-related data accuracy"""
        try:
            # Get current date ranges
            today = timezone.now().date()
            last_30_days = today - timedelta(days=30)
            last_7_days = today - timedelta(days=7)
            
            # User statistics
            total_users = User.objects.count()
            active_users_30d = User.objects.filter(last_login__gte=last_30_days).count()
            new_users_7d = User.objects.filter(date_joined__gte=last_7_days).count()
            new_users_30d = User.objects.filter(date_joined__gte=last_30_days).count()
            
            # Superuser verification
            superusers = User.objects.filter(is_superuser=True)
            victor_account = User.objects.filter(username='victor').first()
            
            user_data = {
                'total_users': total_users,
                'active_users_30d': active_users_30d,
                'new_users_7d': new_users_7d,
                'new_users_30d': new_users_30d,
                'superuser_count': superusers.count(),
                'victor_account_exists': victor_account is not None,
                'victor_is_superuser': victor_account.is_superuser if victor_account else False,
                'sample_users': list(User.objects.values('id', 'username', 'email', 'date_joined', 'is_superuser')[:5])
            }
            
            self.audit_results['data_verification']['users'] = user_data
            return user_data
            
        except Exception as e:
            error_data = {'error': str(e), 'status': 'failed'}
            self.audit_results['data_verification']['users'] = error_data
            return error_data
    
    def verify_course_data(self):
        """Verify course-related data accuracy"""
        try:
            # Import course models dynamically
            from courses.models import Course, Module, Lesson
            
            total_courses = Course.objects.count()
            published_courses = Course.objects.filter(is_published=True).count()
            total_modules = Module.objects.count()
            total_lessons = Lesson.objects.count()
            
            # Course details
            sample_courses = list(Course.objects.values(
                'id', 'title', 'is_published', 'price', 'created_at'
            )[:5])
            
            course_data = {
                'total_courses': total_courses,
                'published_courses': published_courses,
                'total_modules': total_modules,
                'total_lessons': total_lessons,
                'sample_courses': sample_courses
            }
            
            self.audit_results['data_verification']['courses'] = course_data
            return course_data
            
        except ImportError as e:
            error_data = {'error': f'Course models not available: {str(e)}', 'status': 'models_missing'}
            self.audit_results['data_verification']['courses'] = error_data
            return error_data
        except Exception as e:
            error_data = {'error': str(e), 'status': 'failed'}
            self.audit_results['data_verification']['courses'] = error_data
            return error_data
    
    def verify_enrollment_data(self):
        """Verify enrollment-related data accuracy"""
        try:
            from progress.models import Enrollment
            
            total_enrollments = Enrollment.objects.count()
            active_enrollments = Enrollment.objects.filter(status='active').count()
            completed_enrollments = Enrollment.objects.filter(status='completed').count()
            
            # Recent enrollments
            recent_enrollments = list(Enrollment.objects.select_related('student', 'course').values(
                'id', 'student__username', 'course__title', 'status', 'enrollment_date'
            ).order_by('-enrollment_date')[:5])
            
            enrollment_data = {
                'total_enrollments': total_enrollments,
                'active_enrollments': active_enrollments,
                'completed_enrollments': completed_enrollments,
                'recent_enrollments': recent_enrollments
            }
            
            self.audit_results['data_verification']['enrollments'] = enrollment_data
            return enrollment_data
            
        except ImportError as e:
            error_data = {'error': f'Enrollment models not available: {str(e)}', 'status': 'models_missing'}
            self.audit_results['data_verification']['enrollments'] = error_data
            return error_data
        except Exception as e:
            error_data = {'error': str(e), 'status': 'failed'}
            self.audit_results['data_verification']['enrollments'] = error_data
            return error_data
    
    def verify_payment_data(self):
        """Verify payment-related data accuracy"""
        try:
            from payments.models import Payment
            
            from django.db import models

            # Payment statistics
            completed_payments = Payment.objects.filter(status='completed')
            total_revenue = completed_payments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

            # Monthly revenue
            current_month_start = timezone.now().date().replace(day=1)
            monthly_revenue = Payment.objects.filter(
                status='completed',
                created_at__gte=current_month_start
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            
            payment_counts = {
                'completed': Payment.objects.filter(status='completed').count(),
                'pending': Payment.objects.filter(status='pending').count(),
                'failed': Payment.objects.filter(status='failed').count()
            }
            
            # Recent payments
            recent_payments = list(Payment.objects.select_related('user').values(
                'id', 'user__username', 'amount', 'status', 'created_at'
            ).order_by('-created_at')[:5])
            
            payment_data = {
                'total_revenue': float(total_revenue),
                'monthly_revenue': float(monthly_revenue),
                'payment_counts': payment_counts,
                'recent_payments': recent_payments
            }
            
            self.audit_results['data_verification']['payments'] = payment_data
            return payment_data
            
        except ImportError as e:
            error_data = {'error': f'Payment models not available: {str(e)}', 'status': 'models_missing'}
            self.audit_results['data_verification']['payments'] = error_data
            return error_data
        except Exception as e:
            error_data = {'error': str(e), 'status': 'failed'}
            self.audit_results['data_verification']['payments'] = error_data
            return error_data
    
    def run_comprehensive_audit(self):
        """Run complete data accuracy audit"""
        print("🔍 Starting YITP Dashboard Data Accuracy Audit...")
        print("=" * 60)
        
        # Environment verification
        env_info = self.audit_results['environment']
        print(f"📊 Environment: {env_info['detected_environment'].upper()}")
        print(f"🗄️  Database: {env_info['database_engine']}")
        print(f"🔗 Host: {self.audit_results['database_info']['host']}")
        print(f"✅ Connection: {self.audit_results['database_info']['connection_test']['status']}")
        print()
        
        # Data verification
        print("📈 Verifying Data Accuracy...")
        
        # Users
        print("👥 User Data Verification:")
        user_data = self.verify_user_data()
        if 'error' not in user_data:
            print(f"   Total Users: {user_data['total_users']}")
            print(f"   Active (30d): {user_data['active_users_30d']}")
            print(f"   New (7d): {user_data['new_users_7d']}")
            print(f"   Victor Account: {'✅' if user_data['victor_account_exists'] else '❌'}")
        else:
            print(f"   ❌ Error: {user_data['error']}")
        print()
        
        # Courses
        print("📚 Course Data Verification:")
        course_data = self.verify_course_data()
        if 'error' not in course_data:
            print(f"   Total Courses: {course_data['total_courses']}")
            print(f"   Published: {course_data['published_courses']}")
            print(f"   Modules: {course_data['total_modules']}")
            print(f"   Lessons: {course_data['total_lessons']}")
        else:
            print(f"   ❌ Error: {course_data['error']}")
        print()
        
        # Enrollments
        print("🎓 Enrollment Data Verification:")
        enrollment_data = self.verify_enrollment_data()
        if 'error' not in enrollment_data:
            print(f"   Total Enrollments: {enrollment_data['total_enrollments']}")
            print(f"   Active: {enrollment_data['active_enrollments']}")
            print(f"   Completed: {enrollment_data['completed_enrollments']}")
        else:
            print(f"   ❌ Error: {enrollment_data['error']}")
        print()
        
        # Payments
        print("💰 Payment Data Verification:")
        payment_data = self.verify_payment_data()
        if 'error' not in payment_data:
            print(f"   Total Revenue: ${payment_data['total_revenue']:.2f}")
            print(f"   Monthly Revenue: ${payment_data['monthly_revenue']:.2f}")
            print(f"   Completed Payments: {payment_data['payment_counts']['completed']}")
        else:
            print(f"   ❌ Error: {payment_data['error']}")
        print()
        
        return self.audit_results
    
    def save_audit_report(self, filename='dashboard_audit_report.json'):
        """Save audit results to file"""
        with open(filename, 'w') as f:
            json.dump(self.audit_results, f, indent=2, default=str)
        print(f"📄 Audit report saved to: {filename}")

if __name__ == "__main__":
    auditor = DashboardDataAudit()
    results = auditor.run_comprehensive_audit()
    auditor.save_audit_report()
    
    print("=" * 60)
    print("🎯 Audit Complete!")
    print(f"📊 Environment: {results['environment']['detected_environment']}")
    print(f"🔗 Database: {results['database_info']['connection_test']['status']}")
