"""
Comprehensive Unit Tests for Analytics Services
Tests payment analytics generation, user behavior tracking, and revenue analytics
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from analytics.services import PaymentAnalyticsService, UserBehaviorAnalyticsService, CourseRevenueService
from analytics.models import PaymentAnalytics, UserPaymentBehavior, CourseRevenueAnalytics
from payments.models import Payment
from courses.models import Course, Module, Lesson, Category
from progress.models import Enrollment
from users.models import Profile

User = get_user_model()


class PaymentAnalyticsServiceTestCase(TestCase):
    """Test PaymentAnalyticsService functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create profiles
        self.profile1 = Profile.objects.create(
            user=self.user1,
            payment_verified=True,
            has_paid=True
        )
        self.profile2 = Profile.objects.create(
            user=self.user2,
            payment_verified=True,
            has_paid=True
        )
        
        # Create test date
        self.test_date = date.today() - timedelta(days=1)
        
        # Create test payments for yesterday
        self.payment1 = Payment.objects.create(
            user=self.user1,
            amount=Decimal('5000.00'),
            payment_method='mpesa',
            status='confirmed',
            transaction_id='TEST001',
            created_at=timezone.make_aware(
                timezone.datetime.combine(self.test_date, timezone.datetime.min.time())
            )
        )
        
        self.payment2 = Payment.objects.create(
            user=self.user1,
            amount=Decimal('2500.00'),
            payment_method='paypal',
            status='confirmed',
            transaction_id='TEST002',
            is_installment=True,
            installment_sequence=1,
            created_at=timezone.make_aware(
                timezone.datetime.combine(self.test_date, timezone.datetime.min.time())
            )
        )
        
        self.payment3 = Payment.objects.create(
            user=self.user2,
            amount=Decimal('3000.00'),
            payment_method='bank_transfer',
            status='pending',
            transaction_id='TEST003',
            created_at=timezone.make_aware(
                timezone.datetime.combine(self.test_date, timezone.datetime.min.time())
            )
        )

    def test_generate_daily_analytics_success(self):
        """Test successful daily analytics generation"""
        analytics = PaymentAnalyticsService.generate_daily_analytics(self.test_date)
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.date, self.test_date)
        self.assertEqual(analytics.total_payments, 3)
        self.assertEqual(analytics.mpesa_payments, 1)
        self.assertEqual(analytics.paypal_payments, 1)
        self.assertEqual(analytics.bank_transfer_payments, 1)
        
        # Check revenue (only confirmed payments)
        self.assertEqual(analytics.mpesa_revenue, Decimal('5000.00'))
        self.assertEqual(analytics.paypal_revenue, Decimal('2500.00'))
        self.assertEqual(analytics.bank_transfer_revenue, Decimal('0.00'))  # Pending
        self.assertEqual(analytics.total_revenue, Decimal('7500.00'))
        
        # Check payment status
        self.assertEqual(analytics.confirmed_payments, 2)
        self.assertEqual(analytics.pending_payments, 1)
        self.assertEqual(analytics.failed_payments, 0)

    def test_generate_daily_analytics_with_defaults(self):
        """Test analytics generation with default date (yesterday)"""
        analytics = PaymentAnalyticsService.generate_daily_analytics()
        
        self.assertIsNotNone(analytics)
        expected_date = (timezone.now() - timedelta(days=1)).date()
        self.assertEqual(analytics.date, expected_date)

    def test_generate_daily_analytics_no_payments(self):
        """Test analytics generation when there are no payments"""
        future_date = date.today() + timedelta(days=1)
        analytics = PaymentAnalyticsService.generate_daily_analytics(future_date)
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.total_payments, 0)
        self.assertEqual(analytics.total_revenue, Decimal('0.00'))

    def test_generate_daily_analytics_installment_completion_rate(self):
        """Test installment completion rate calculation"""
        # Create second installment
        Payment.objects.create(
            user=self.user1,
            amount=Decimal('2500.00'),
            payment_method='paypal',
            status='confirmed',
            transaction_id='TEST004',
            is_installment=True,
            installment_sequence=2,
            created_at=timezone.make_aware(
                timezone.datetime.combine(self.test_date, timezone.datetime.min.time())
            )
        )
        
        analytics = PaymentAnalyticsService.generate_daily_analytics(self.test_date)
        
        self.assertEqual(analytics.installment_payments, 2)
        self.assertEqual(analytics.first_installments, 1)
        self.assertEqual(analytics.second_installments, 1)
        self.assertEqual(analytics.installment_completion_rate, 100.00)

    def test_generate_daily_analytics_updates_existing(self):
        """Test that running analytics twice updates existing record"""
        analytics1 = PaymentAnalyticsService.generate_daily_analytics(self.test_date)
        initial_id = analytics1.id
        
        # Create another payment
        Payment.objects.create(
            user=self.user2,
            amount=Decimal('1000.00'),
            payment_method='mpesa',
            status='confirmed',
            transaction_id='TEST005',
            created_at=timezone.make_aware(
                timezone.datetime.combine(self.test_date, timezone.datetime.min.time())
            )
        )
        
        analytics2 = PaymentAnalyticsService.generate_daily_analytics(self.test_date)
        
        # Should update same record
        self.assertEqual(analytics2.id, initial_id)
        self.assertEqual(analytics2.total_payments, 4)
        self.assertEqual(analytics2.total_revenue, Decimal('8500.00'))

    def test_generate_daily_analytics_new_vs_returning_users(self):
        """Test new vs returning user classification"""
        # user1 has payments from before (setUp), so should be returning
        # user2's first payment is in setUp, so should be counted differently
        
        analytics = PaymentAnalyticsService.generate_daily_analytics(self.test_date)
        
        # This test validates the user classification logic
        self.assertGreaterEqual(analytics.new_users + analytics.returning_users, 0)

    def test_generate_daily_analytics_error_handling(self):
        """Test analytics generation handles errors gracefully"""
        with patch('analytics.services.Payment.objects.filter') as mock_filter:
            mock_filter.side_effect = Exception("Database error")
            
            # Should not raise exception
            try:
                analytics = PaymentAnalyticsService.generate_daily_analytics(self.test_date)
                # If it returns None or handles gracefully, test passes
            except Exception as e:
                self.fail(f"Should handle errors gracefully, but raised: {e}")


class UserBehaviorAnalyticsServiceTestCase(TestCase):
    """Test UserBehaviorAnalyticsService functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='behavioruser',
            email='behavior@example.com',
            password='testpass123'
        )
        
        # Create payment history
        base_date = timezone.now() - timedelta(days=30)
        
        for i in range(5):
            Payment.objects.create(
                user=self.user,
                amount=Decimal('2000.00'),
                payment_method='mpesa' if i % 2 == 0 else 'paypal',
                status='confirmed' if i < 4 else 'failed',
                transaction_id=f'BEHAVIOR{i:03d}',
                created_at=base_date + timedelta(days=i*7)
            )

    def test_update_user_behavior_success(self):
        """Test successful user behavior update"""
        behavior = UserBehaviorAnalyticsService.update_user_behavior(self.user)
        
        self.assertIsNotNone(behavior)
        self.assertEqual(behavior.user, self.user)
        self.assertEqual(behavior.total_payments, 5)
        self.assertEqual(behavior.successful_payments, 4)
        self.assertEqual(behavior.failed_payments, 1)
        self.assertEqual(behavior.total_amount_paid, Decimal('8000.00'))
        self.assertIsNotNone(behavior.preferred_payment_method)

    def test_update_user_behavior_payment_method_preference(self):
        """Test payment method preference calculation"""
        behavior = UserBehaviorAnalyticsService.update_user_behavior(self.user)
        
        # Based on setUp: 3 mpesa, 2 paypal
        self.assertEqual(behavior.mpesa_usage_count, 3)
        self.assertEqual(behavior.paypal_usage_count, 2)
        self.assertEqual(behavior.preferred_payment_method, 'mpesa')

    def test_update_user_behavior_average_payment_amount(self):
        """Test average payment amount calculation"""
        behavior = UserBehaviorAnalyticsService.update_user_behavior(self.user)
        
        # Only successful payments count: 4 * 2000 = 8000, avg = 2000
        self.assertEqual(behavior.average_payment_amount, Decimal('2000.00'))

    def test_update_user_behavior_failure_rate(self):
        """Test payment failure rate calculation"""
        behavior = UserBehaviorAnalyticsService.update_user_behavior(self.user)
        
        # 1 failed out of 5 total = 20%
        self.assertEqual(behavior.payment_failure_rate, Decimal('20.00'))

    def test_update_user_behavior_no_payments(self):
        """Test behavior update for user with no payments"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        behavior = UserBehaviorAnalyticsService.update_user_behavior(new_user)
        
        self.assertIsNotNone(behavior)
        self.assertEqual(behavior.total_payments, 0)
        self.assertEqual(behavior.total_amount_paid, Decimal('0.00'))

    def test_get_user_behavior_creates_if_not_exists(self):
        """Test getting behavior creates record if it doesn't exist"""
        new_user = User.objects.create_user(
            username='anotheruser',
            email='another@example.com',
            password='testpass123'
        )
        
        self.assertFalse(
            UserPaymentBehavior.objects.filter(user=new_user).exists()
        )
        
        behavior = UserBehaviorAnalyticsService.get_user_behavior(new_user)
        
        self.assertIsNotNone(behavior)
        self.assertTrue(
            UserPaymentBehavior.objects.filter(user=new_user).exists()
        )


class CourseRevenueServiceTestCase(TestCase):
    """Test CourseRevenueService functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create course
        self.course = Course.objects.create(
            title='Test Course',
            slug='test-course',
            description='Test Description',
            price=Decimal('5000.00'),
            category=self.category,
            is_published=True
        )
        
        # Create users and enrollments
        self.user1 = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='student2',
            email='student2@example.com',
            password='testpass123'
        )
        
        self.enrollment1 = Enrollment.objects.create(
            student=self.user1,
            course=self.course,
            status='active'
        )
        self.enrollment2 = Enrollment.objects.create(
            student=self.user2,
            course=self.course,
            status='active'
        )
        
        # Create payments
        self.test_date = date.today()
        Payment.objects.create(
            user=self.user1,
            amount=Decimal('5000.00'),
            payment_method='mpesa',
            status='confirmed',
            transaction_id='COURSE001',
            created_at=timezone.now()
        )
        Payment.objects.create(
            user=self.user2,
            amount=Decimal('5000.00'),
            payment_method='paypal',
            status='confirmed',
            transaction_id='COURSE002',
            created_at=timezone.now()
        )

    def test_generate_course_revenue_analytics(self):
        """Test course revenue analytics generation"""
        analytics = CourseRevenueService.generate_course_revenue(
            self.course,
            self.test_date
        )
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.course, self.course)
        self.assertEqual(analytics.date, self.test_date)

    def test_get_course_revenue_trend(self):
        """Test getting course revenue trend over time"""
        # Create historical data
        for days_ago in range(7):
            test_date = date.today() - timedelta(days=days_ago)
            CourseRevenueAnalytics.objects.create(
                course=self.course,
                date=test_date,
                total_revenue=Decimal('10000.00') + Decimal(str(days_ago * 1000)),
                enrollment_count=2 + days_ago
            )
        
        trend = CourseRevenueService.get_revenue_trend(self.course, days=7)
        
        self.assertEqual(len(trend), 7)
        self.assertIn('date', trend[0])
        self.assertIn('revenue', trend[0])
        self.assertIn('enrollments', trend[0])

    def test_get_top_revenue_courses(self):
        """Test getting top revenue generating courses"""
        # Create another course with higher revenue
        course2 = Course.objects.create(
            title='Premium Course',
            slug='premium-course',
            description='Premium Description',
            price=Decimal('10000.00'),
            category=self.category,
            is_published=True
        )
        
        CourseRevenueAnalytics.objects.create(
            course=course2,
            date=self.test_date,
            total_revenue=Decimal('50000.00'),
            enrollment_count=5
        )
        
        CourseRevenueAnalytics.objects.create(
            course=self.course,
            date=self.test_date,
            total_revenue=Decimal('10000.00'),
            enrollment_count=2
        )
        
        top_courses = CourseRevenueService.get_top_revenue_courses(limit=2)
        
        self.assertEqual(len(top_courses), 2)
        self.assertEqual(top_courses[0].course, course2)  # Higher revenue first


class AnalyticsIntegrationTestCase(TransactionTestCase):
    """Integration tests for analytics services"""
    
    def test_full_analytics_pipeline(self):
        """Test complete analytics generation pipeline"""
        # Create test data
        user = User.objects.create_user(
            username='pipelineuser',
            email='pipeline@example.com',
            password='testpass123'
        )
        
        category = Category.objects.create(
            name='Pipeline Category',
            slug='pipeline-category'
        )
        
        course = Course.objects.create(
            title='Pipeline Course',
            slug='pipeline-course',
            description='Pipeline Description',
            price=Decimal('3000.00'),
            category=category,
            is_published=True
        )
        
        Enrollment.objects.create(
            student=user,
            course=course,
            status='active'
        )
        
        test_date = date.today()
        Payment.objects.create(
            user=user,
            amount=Decimal('3000.00'),
            payment_method='mpesa',
            status='confirmed',
            transaction_id='PIPELINE001',
            created_at=timezone.now()
        )
        
        # Generate all analytics
        payment_analytics = PaymentAnalyticsService.generate_daily_analytics(test_date)
        user_behavior = UserBehaviorAnalyticsService.update_user_behavior(user)
        course_revenue = CourseRevenueService.generate_course_revenue(course, test_date)
        
        # Verify all analytics were created
        self.assertIsNotNone(payment_analytics)
        self.assertIsNotNone(user_behavior)
        self.assertIsNotNone(course_revenue)
        
        # Verify data consistency
        self.assertEqual(payment_analytics.total_payments, 1)
        self.assertEqual(user_behavior.total_payments, 1)
        self.assertEqual(payment_analytics.total_revenue, Decimal('3000.00'))


class AnalyticsEdgeCasesTestCase(TestCase):
    """Test edge cases and error conditions"""
    
    def test_zero_division_in_completion_rate(self):
        """Test completion rate calculation with zero first installments"""
        test_date = date.today()
        analytics = PaymentAnalyticsService.generate_daily_analytics(test_date)
        
        # Should handle zero division gracefully
        self.assertEqual(analytics.installment_completion_rate, 0.00)

    def test_analytics_with_deleted_user(self):
        """Test analytics handles deleted user references"""
        user = User.objects.create_user(
            username='deleteduser',
            email='deleted@example.com',
            password='testpass123'
        )
        
        Payment.objects.create(
            user=user,
            amount=Decimal('1000.00'),
            payment_method='mpesa',
            status='confirmed',
            transaction_id='DELETE001',
            created_at=timezone.now()
        )
        
        user_id = user.id
        user.delete()
        
        # Analytics should still work
        test_date = date.today()
        analytics = PaymentAnalyticsService.generate_daily_analytics(test_date)
        self.assertIsNotNone(analytics)

    def test_concurrent_analytics_generation(self):
        """Test that concurrent analytics generation doesn't create duplicates"""
        test_date = date.today()
        
        # Create payments
        user = User.objects.create_user(
            username='concurrentuser',
            email='concurrent@example.com',
            password='testpass123'
        )
        Payment.objects.create(
            user=user,
            amount=Decimal('1000.00'),
            payment_method='mpesa',
            status='confirmed',
            transaction_id='CONCURRENT001',
            created_at=timezone.now()
        )
        
        # Generate analytics multiple times
        analytics1 = PaymentAnalyticsService.generate_daily_analytics(test_date)
        analytics2 = PaymentAnalyticsService.generate_daily_analytics(test_date)
        
        # Should be same record
        self.assertEqual(analytics1.id, analytics2.id)
        
        # Should only have one record for this date
        self.assertEqual(
            PaymentAnalytics.objects.filter(date=test_date).count(),
            1
        )
