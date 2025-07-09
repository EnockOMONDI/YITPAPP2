"""
Analytics Models for YITP Payment Insights
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal


class PaymentAnalytics(models.Model):
    """
    Daily aggregated payment analytics data
    """
    date = models.DateField(unique=True)
    
    # Payment counts by method
    mpesa_payments = models.IntegerField(default=0)
    bank_transfer_payments = models.IntegerField(default=0)
    paypal_payments = models.IntegerField(default=0)
    total_payments = models.IntegerField(default=0)
    
    # Payment amounts by method
    mpesa_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    bank_transfer_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paypal_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Payment status counts
    confirmed_payments = models.IntegerField(default=0)
    pending_payments = models.IntegerField(default=0)
    failed_payments = models.IntegerField(default=0)
    expired_payments = models.IntegerField(default=0)
    
    # Installment analytics
    installment_payments = models.IntegerField(default=0)
    first_installments = models.IntegerField(default=0)
    second_installments = models.IntegerField(default=0)
    installment_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # User behavior
    new_users = models.IntegerField(default=0)
    returning_users = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name = "Payment Analytics"
        verbose_name_plural = "Payment Analytics"
    
    def __str__(self):
        return f"Analytics for {self.date}"


class UserPaymentBehavior(models.Model):
    """
    Track individual user payment behavior patterns
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='payment_behavior')
    
    # Payment history
    total_payments = models.IntegerField(default=0)
    successful_payments = models.IntegerField(default=0)
    failed_payments = models.IntegerField(default=0)
    
    # Payment methods preference
    preferred_payment_method = models.CharField(max_length=20, blank=True)
    mpesa_usage_count = models.IntegerField(default=0)
    bank_transfer_usage_count = models.IntegerField(default=0)
    paypal_usage_count = models.IntegerField(default=0)
    
    # Financial metrics
    total_amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Installment behavior
    installment_payments_made = models.IntegerField(default=0)
    installment_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Timing patterns
    first_payment_date = models.DateTimeField(null=True, blank=True)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    average_days_between_payments = models.IntegerField(default=0)
    
    # Risk indicators
    payment_failure_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    late_payment_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Payment Behavior"
        verbose_name_plural = "User Payment Behaviors"
    
    def __str__(self):
        return f"Payment behavior for {self.user.username}"
    
    def update_behavior(self):
        """Update behavior metrics based on user's payment history"""
        from payments.models import Payment
        
        payments = Payment.objects.filter(user=self.user)
        
        self.total_payments = payments.count()
        self.successful_payments = payments.filter(status='confirmed').count()
        self.failed_payments = payments.filter(status='failed').count()
        
        # Calculate payment method preference
        method_counts = {
            'mpesa': payments.filter(payment_method='mpesa').count(),
            'bank_transfer': payments.filter(payment_method='bank_transfer').count(),
            'paypal': payments.filter(payment_method='paypal').count(),
        }
        
        self.mpesa_usage_count = method_counts['mpesa']
        self.bank_transfer_usage_count = method_counts['bank_transfer']
        self.paypal_usage_count = method_counts['paypal']
        
        # Determine preferred method
        if method_counts:
            self.preferred_payment_method = max(method_counts, key=method_counts.get)
        
        # Financial metrics
        confirmed_payments = payments.filter(status='confirmed')
        if confirmed_payments.exists():
            self.total_amount_paid = sum(p.amount for p in confirmed_payments)
            self.average_payment_amount = self.total_amount_paid / confirmed_payments.count()
            self.first_payment_date = confirmed_payments.order_by('created_at').first().created_at
            self.last_payment_date = confirmed_payments.order_by('created_at').last().created_at
        
        # Installment metrics
        installment_payments = payments.filter(is_installment=True)
        self.installment_payments_made = installment_payments.count()
        
        if installment_payments.exists():
            first_installments = installment_payments.filter(installment_sequence=1).count()
            second_installments = installment_payments.filter(installment_sequence=2).count()
            if first_installments > 0:
                self.installment_completion_rate = (second_installments / first_installments) * 100
        
        # Risk indicators
        if self.total_payments > 0:
            self.payment_failure_rate = (self.failed_payments / self.total_payments) * 100
        
        self.save()


class CourseRevenueAnalytics(models.Model):
    """
    Revenue analytics per course
    """
    course = models.OneToOneField('courses.Course', on_delete=models.CASCADE, related_name='revenue_analytics')
    
    # Enrollment metrics
    total_enrollments = models.IntegerField(default=0)
    paid_enrollments = models.IntegerField(default=0)
    free_enrollments = models.IntegerField(default=0)
    
    # Revenue metrics
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_revenue_per_user = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Payment method breakdown
    mpesa_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    bank_transfer_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    paypal_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Installment metrics
    installment_enrollments = models.IntegerField(default=0)
    installment_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Conversion metrics
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # paid/total enrollments
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Course Revenue Analytics"
        verbose_name_plural = "Course Revenue Analytics"
    
    def __str__(self):
        return f"Revenue analytics for {self.course.title}"
    
    def update_analytics(self):
        """Update analytics based on course enrollments and payments"""
        from progress.models import Enrollment
        from payments.models import Payment
        
        enrollments = Enrollment.objects.filter(course=self.course)
        payments = Payment.objects.filter(course=self.course, status='confirmed')
        
        self.total_enrollments = enrollments.count()
        self.paid_enrollments = payments.count()
        self.free_enrollments = self.total_enrollments - self.paid_enrollments
        
        if payments.exists():
            self.total_revenue = sum(p.amount for p in payments)
            self.average_revenue_per_user = self.total_revenue / payments.count()
            
            # Payment method breakdown
            self.mpesa_revenue = sum(p.amount for p in payments.filter(payment_method='mpesa'))
            self.bank_transfer_revenue = sum(p.amount for p in payments.filter(payment_method='bank_transfer'))
            self.paypal_revenue = sum(p.amount for p in payments.filter(payment_method='paypal'))
            
            # Installment metrics
            installment_payments = payments.filter(is_installment=True)
            self.installment_enrollments = installment_payments.filter(installment_sequence=1).count()
            
            if self.installment_enrollments > 0:
                completed_installments = installment_payments.filter(installment_sequence=2).count()
                self.installment_completion_rate = (completed_installments / self.installment_enrollments) * 100
        
        # Conversion rate
        if self.total_enrollments > 0:
            self.conversion_rate = (self.paid_enrollments / self.total_enrollments) * 100
        
        self.save()
