"""
Analytics Services for YITP Payment Insights
"""

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .models import PaymentAnalytics, UserPaymentBehavior, CourseRevenueAnalytics
from payments.models import Payment
from users.models import Profile
from courses.models import Course
from progress.models import Enrollment

logger = logging.getLogger(__name__)


class PaymentAnalyticsService:
    """Service for generating and managing payment analytics"""
    
    @staticmethod
    def generate_daily_analytics(date=None):
        """
        Generate daily payment analytics for a specific date
        
        Args:
            date: Date to generate analytics for (defaults to yesterday)
            
        Returns:
            PaymentAnalytics: Created or updated analytics record
        """
        if date is None:
            date = (timezone.now() - timedelta(days=1)).date()
        
        try:
            # Get or create analytics record for the date
            analytics, created = PaymentAnalytics.objects.get_or_create(
                date=date,
                defaults={}
            )
            
            # Get payments for the date
            payments = Payment.objects.filter(
                created_at__date=date
            )
            
            # Payment counts by method
            analytics.mpesa_payments = payments.filter(payment_method='mpesa').count()
            analytics.bank_transfer_payments = payments.filter(payment_method='bank_transfer').count()
            analytics.paypal_payments = payments.filter(payment_method='paypal').count()
            analytics.total_payments = payments.count()
            
            # Revenue by method (only confirmed payments)
            confirmed_payments = payments.filter(status='confirmed')
            
            analytics.mpesa_revenue = sum(
                p.amount for p in confirmed_payments.filter(payment_method='mpesa')
            ) or Decimal('0.00')
            
            analytics.bank_transfer_revenue = sum(
                p.amount for p in confirmed_payments.filter(payment_method='bank_transfer')
            ) or Decimal('0.00')
            
            analytics.paypal_revenue = sum(
                p.amount for p in confirmed_payments.filter(payment_method='paypal')
            ) or Decimal('0.00')
            
            analytics.total_revenue = analytics.mpesa_revenue + analytics.bank_transfer_revenue + analytics.paypal_revenue
            
            # Payment status counts
            analytics.confirmed_payments = payments.filter(status='confirmed').count()
            analytics.pending_payments = payments.filter(status='pending').count()
            analytics.failed_payments = payments.filter(status='failed').count()
            analytics.expired_payments = payments.filter(status='expired').count()
            
            # Installment analytics
            installment_payments = payments.filter(is_installment=True)
            analytics.installment_payments = installment_payments.count()
            analytics.first_installments = installment_payments.filter(installment_sequence=1).count()
            analytics.second_installments = installment_payments.filter(installment_sequence=2).count()
            
            if analytics.first_installments > 0:
                analytics.installment_completion_rate = (
                    analytics.second_installments / analytics.first_installments
                ) * 100
            
            # User behavior (new vs returning users who made payments)
            user_ids = payments.values_list('user_id', flat=True).distinct()
            
            # Count new users (first payment ever)
            new_user_count = 0
            returning_user_count = 0
            
            for user_id in user_ids:
                first_payment = Payment.objects.filter(user_id=user_id).order_by('created_at').first()
                if first_payment and first_payment.created_at.date() == date:
                    new_user_count += 1
                else:
                    returning_user_count += 1
            
            analytics.new_users = new_user_count
            analytics.returning_users = returning_user_count
            
            analytics.save()
            
            logger.info(f"Generated daily analytics for {date}: {analytics.total_payments} payments, KES {analytics.total_revenue}")
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to generate daily analytics for {date}: {str(e)}")
            raise
    
    @staticmethod
    def get_revenue_trends(days=30):
        """
        Get revenue trends for the last N days
        
        Args:
            days: Number of days to include in trends
            
        Returns:
            dict: Revenue trend data
        """
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        analytics = PaymentAnalytics.objects.filter(
            date__range=[start_date, end_date]
        ).order_by('date')
        
        return {
            'dates': [a.date.strftime('%Y-%m-%d') for a in analytics],
            'total_revenue': [float(a.total_revenue) for a in analytics],
            'mpesa_revenue': [float(a.mpesa_revenue) for a in analytics],
            'bank_transfer_revenue': [float(a.bank_transfer_revenue) for a in analytics],
            'paypal_revenue': [float(a.paypal_revenue) for a in analytics],
            'payment_counts': [a.total_payments for a in analytics],
        }
    
    @staticmethod
    def get_payment_method_performance():
        """
        Get payment method performance metrics
        
        Returns:
            dict: Payment method performance data
        """
        # Get all-time totals
        total_stats = Payment.objects.filter(status='confirmed').aggregate(
            total_count=Count('id'),
            total_revenue=Sum('amount'),
            mpesa_count=Count('id', filter=Q(payment_method='mpesa')),
            mpesa_revenue=Sum('amount', filter=Q(payment_method='mpesa')),
            bank_transfer_count=Count('id', filter=Q(payment_method='bank_transfer')),
            bank_transfer_revenue=Sum('amount', filter=Q(payment_method='bank_transfer')),
            paypal_count=Count('id', filter=Q(payment_method='paypal')),
            paypal_revenue=Sum('amount', filter=Q(payment_method='paypal')),
        )
        
        # Calculate success rates by method
        success_rates = {}
        for method in ['mpesa', 'bank_transfer', 'paypal']:
            total_attempts = Payment.objects.filter(payment_method=method).count()
            successful = Payment.objects.filter(payment_method=method, status='confirmed').count()
            success_rates[method] = (successful / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            'totals': total_stats,
            'success_rates': success_rates,
            'method_breakdown': {
                'mpesa': {
                    'count': total_stats['mpesa_count'] or 0,
                    'revenue': float(total_stats['mpesa_revenue'] or 0),
                    'success_rate': success_rates['mpesa'],
                },
                'bank_transfer': {
                    'count': total_stats['bank_transfer_count'] or 0,
                    'revenue': float(total_stats['bank_transfer_revenue'] or 0),
                    'success_rate': success_rates['bank_transfer'],
                },
                'paypal': {
                    'count': total_stats['paypal_count'] or 0,
                    'revenue': float(total_stats['paypal_revenue'] or 0),
                    'success_rate': success_rates['paypal'],
                },
            }
        }
    
    @staticmethod
    def get_installment_analytics():
        """
        Get installment payment analytics
        
        Returns:
            dict: Installment analytics data
        """
        # Overall installment metrics
        total_first_installments = Payment.objects.filter(
            is_installment=True,
            installment_sequence=1,
            status='confirmed'
        ).count()
        
        total_second_installments = Payment.objects.filter(
            is_installment=True,
            installment_sequence=2,
            status='confirmed'
        ).count()
        
        completion_rate = (
            total_second_installments / total_first_installments * 100
        ) if total_first_installments > 0 else 0
        
        # Installment revenue
        installment_revenue = Payment.objects.filter(
            is_installment=True,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        # Time-based completion analysis
        profiles_with_partial = Profile.objects.filter(payment_status='partially_paid')
        
        return {
            'total_first_installments': total_first_installments,
            'total_second_installments': total_second_installments,
            'completion_rate': round(completion_rate, 2),
            'installment_revenue': float(installment_revenue),
            'active_partial_payments': profiles_with_partial.count(),
            'expired_partial_payments': Profile.objects.filter(payment_status='expired').count(),
        }
    
    @staticmethod
    def update_user_behavior_analytics():
        """
        Update payment behavior analytics for all users
        """
        updated_count = 0
        
        # Get all users who have made payments
        user_ids = Payment.objects.values_list('user_id', flat=True).distinct()
        
        for user_id in user_ids:
            try:
                behavior, created = UserPaymentBehavior.objects.get_or_create(
                    user_id=user_id
                )
                behavior.update_behavior()
                updated_count += 1
                
            except Exception as e:
                logger.error(f"Failed to update behavior for user {user_id}: {str(e)}")
        
        logger.info(f"Updated payment behavior analytics for {updated_count} users")
        return updated_count
    
    @staticmethod
    def update_course_revenue_analytics():
        """
        Update revenue analytics for all courses
        """
        updated_count = 0
        
        # Get all courses that have payments
        course_ids = Payment.objects.filter(
            status='confirmed'
        ).values_list('course_id', flat=True).distinct()
        
        for course_id in course_ids:
            try:
                course = Course.objects.get(id=course_id)
                analytics, created = CourseRevenueAnalytics.objects.get_or_create(
                    course=course
                )
                analytics.update_analytics()
                updated_count += 1
                
            except Course.DoesNotExist:
                logger.warning(f"Course {course_id} not found for analytics update")
            except Exception as e:
                logger.error(f"Failed to update analytics for course {course_id}: {str(e)}")
        
        logger.info(f"Updated revenue analytics for {updated_count} courses")
        return updated_count

    @staticmethod
    def get_dashboard_summary():
        """
        Get summary data for the analytics dashboard

        Returns:
            dict: Dashboard summary data
        """
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        last_30_days = today - timedelta(days=30)

        # Today's metrics
        today_payments = Payment.objects.filter(created_at__date=today)
        today_revenue = today_payments.filter(status='confirmed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # Yesterday's metrics for comparison
        yesterday_payments = Payment.objects.filter(created_at__date=yesterday)
        yesterday_revenue = yesterday_payments.filter(status='confirmed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # 30-day metrics
        month_payments = Payment.objects.filter(created_at__date__gte=last_30_days)
        month_revenue = month_payments.filter(status='confirmed').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        # Active users with payments
        active_users = Profile.objects.filter(
            payment_status__in=['confirmed', 'partially_paid']
        ).count()

        # Pending verifications
        pending_verifications = Payment.objects.filter(status='pending').count()

        return {
            'today': {
                'payments': today_payments.count(),
                'revenue': float(today_revenue),
                'confirmed': today_payments.filter(status='confirmed').count(),
            },
            'yesterday': {
                'payments': yesterday_payments.count(),
                'revenue': float(yesterday_revenue),
            },
            'month': {
                'payments': month_payments.count(),
                'revenue': float(month_revenue),
                'confirmed': month_payments.filter(status='confirmed').count(),
            },
            'active_users': active_users,
            'pending_verifications': pending_verifications,
        }
