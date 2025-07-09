"""
Django Admin Configuration for Analytics Models
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import PaymentAnalytics, UserPaymentBehavior, CourseRevenueAnalytics


@admin.register(PaymentAnalytics)
class PaymentAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'total_payments', 'total_revenue_display', 
        'confirmed_payments', 'pending_payments', 'failed_payments',
        'installment_completion_rate_display'
    ]
    list_filter = ['date', 'created_at']
    search_fields = ['date']
    ordering = ['-date']
    readonly_fields = [
        'created_at', 'updated_at', 'total_revenue_display',
        'installment_completion_rate_display', 'payment_breakdown'
    ]
    
    fieldsets = (
        ('Date Information', {
            'fields': ('date', 'created_at', 'updated_at')
        }),
        ('Payment Counts', {
            'fields': (
                'total_payments', 'confirmed_payments', 'pending_payments', 
                'failed_payments', 'expired_payments'
            )
        }),
        ('Payment Methods', {
            'fields': (
                'mpesa_payments', 'bank_transfer_payments', 'paypal_payments'
            )
        }),
        ('Revenue', {
            'fields': (
                'total_revenue_display', 'mpesa_revenue', 
                'bank_transfer_revenue', 'paypal_revenue'
            )
        }),
        ('Installments', {
            'fields': (
                'installment_payments', 'first_installments', 
                'second_installments', 'installment_completion_rate_display'
            )
        }),
        ('User Behavior', {
            'fields': ('new_users', 'returning_users')
        }),
        ('Breakdown', {
            'fields': ('payment_breakdown',),
            'classes': ('collapse',)
        })
    )
    
    def total_revenue_display(self, obj):
        return format_html(
            '<strong style="color: #28a745;">KES {:,.0f}</strong>',
            obj.total_revenue
        )
    total_revenue_display.short_description = 'Total Revenue'
    
    def installment_completion_rate_display(self, obj):
        rate = obj.installment_completion_rate
        color = '#28a745' if rate >= 80 else '#ffc107' if rate >= 60 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    installment_completion_rate_display.short_description = 'Completion Rate'
    
    def payment_breakdown(self, obj):
        return format_html(
            '''
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <h4>Payment Method Breakdown</h4>
                <table style="width: 100%; margin-top: 10px;">
                    <tr>
                        <td><strong>M-Pesa:</strong></td>
                        <td>{} payments</td>
                        <td>KES {:,.0f}</td>
                    </tr>
                    <tr>
                        <td><strong>Bank Transfer:</strong></td>
                        <td>{} payments</td>
                        <td>KES {:,.0f}</td>
                    </tr>
                    <tr>
                        <td><strong>PayPal:</strong></td>
                        <td>{} payments</td>
                        <td>KES {:,.0f}</td>
                    </tr>
                </table>
            </div>
            ''',
            obj.mpesa_payments, obj.mpesa_revenue,
            obj.bank_transfer_payments, obj.bank_transfer_revenue,
            obj.paypal_payments, obj.paypal_revenue
        )
    payment_breakdown.short_description = 'Payment Breakdown'


@admin.register(UserPaymentBehavior)
class UserPaymentBehaviorAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'total_payments', 'successful_payments',
        'total_amount_paid_display', 'preferred_payment_method',
        'payment_failure_rate_display', 'risk_level'
    ]
    list_filter = [
        'preferred_payment_method', 'payment_failure_rate',
        'created_at', 'updated_at'
    ]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    ordering = ['-total_amount_paid']
    readonly_fields = [
        'created_at', 'updated_at', 'total_amount_paid_display',
        'payment_failure_rate_display', 'risk_level', 'payment_summary'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'created_at', 'updated_at')
        }),
        ('Payment History', {
            'fields': (
                'total_payments', 'successful_payments', 'failed_payments',
                'total_amount_paid_display', 'average_payment_amount'
            )
        }),
        ('Payment Methods', {
            'fields': (
                'preferred_payment_method', 'mpesa_usage_count',
                'bank_transfer_usage_count', 'paypal_usage_count'
            )
        }),
        ('Installment Behavior', {
            'fields': (
                'installment_payments_made', 'installment_completion_rate'
            )
        }),
        ('Risk Analysis', {
            'fields': (
                'payment_failure_rate_display', 'late_payment_count', 'risk_level'
            )
        }),
        ('Timing Patterns', {
            'fields': (
                'first_payment_date', 'last_payment_date', 'average_days_between_payments'
            )
        }),
        ('Summary', {
            'fields': ('payment_summary',),
            'classes': ('collapse',)
        })
    )
    
    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    
    def total_amount_paid_display(self, obj):
        return format_html(
            '<strong style="color: #28a745;">KES {:,.0f}</strong>',
            obj.total_amount_paid
        )
    total_amount_paid_display.short_description = 'Total Paid'
    
    def payment_failure_rate_display(self, obj):
        rate = obj.payment_failure_rate
        color = '#dc3545' if rate > 50 else '#ffc107' if rate > 20 else '#28a745'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    payment_failure_rate_display.short_description = 'Failure Rate'
    
    def risk_level(self, obj):
        if obj.payment_failure_rate > 50:
            return format_html('<span style="color: #dc3545; font-weight: bold;">HIGH RISK</span>')
        elif obj.payment_failure_rate > 20:
            return format_html('<span style="color: #ffc107; font-weight: bold;">MEDIUM RISK</span>')
        else:
            return format_html('<span style="color: #28a745; font-weight: bold;">LOW RISK</span>')
    risk_level.short_description = 'Risk Level'
    
    def payment_summary(self, obj):
        return format_html(
            '''
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <h4>Payment Summary for {}</h4>
                <p><strong>Email:</strong> {}</p>
                <p><strong>Success Rate:</strong> {:.1f}%</p>
                <p><strong>Average Payment:</strong> KES {:,.0f}</p>
                <p><strong>Installment Completion:</strong> {:.1f}%</p>
            </div>
            ''',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email,
            100 - obj.payment_failure_rate,
            obj.average_payment_amount,
            obj.installment_completion_rate
        )
    payment_summary.short_description = 'Payment Summary'


@admin.register(CourseRevenueAnalytics)
class CourseRevenueAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'course_link', 'total_enrollments', 'paid_enrollments',
        'total_revenue_display', 'conversion_rate_display',
        'installment_completion_rate_display'
    ]
    list_filter = ['created_at', 'updated_at']
    search_fields = ['course__title', 'course__slug']
    ordering = ['-total_revenue']
    readonly_fields = [
        'created_at', 'updated_at', 'total_revenue_display',
        'conversion_rate_display', 'installment_completion_rate_display',
        'revenue_breakdown'
    ]
    
    fieldsets = (
        ('Course Information', {
            'fields': ('course', 'created_at', 'updated_at')
        }),
        ('Enrollment Metrics', {
            'fields': (
                'total_enrollments', 'paid_enrollments', 'free_enrollments',
                'conversion_rate_display'
            )
        }),
        ('Revenue Metrics', {
            'fields': (
                'total_revenue_display', 'average_revenue_per_user'
            )
        }),
        ('Payment Method Revenue', {
            'fields': (
                'mpesa_revenue', 'bank_transfer_revenue', 'paypal_revenue'
            )
        }),
        ('Installment Metrics', {
            'fields': (
                'installment_enrollments', 'installment_completion_rate_display'
            )
        }),
        ('Breakdown', {
            'fields': ('revenue_breakdown',),
            'classes': ('collapse',)
        })
    )
    
    def course_link(self, obj):
        return format_html('<a href="{}">{}</a>', 
                         reverse('admin:courses_course_change', args=[obj.course.pk]),
                         obj.course.title)
    course_link.short_description = 'Course'
    
    def total_revenue_display(self, obj):
        return format_html(
            '<strong style="color: #28a745;">KES {:,.0f}</strong>',
            obj.total_revenue
        )
    total_revenue_display.short_description = 'Total Revenue'
    
    def conversion_rate_display(self, obj):
        rate = obj.conversion_rate
        color = '#28a745' if rate >= 50 else '#ffc107' if rate >= 25 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    conversion_rate_display.short_description = 'Conversion Rate'
    
    def installment_completion_rate_display(self, obj):
        rate = obj.installment_completion_rate
        color = '#28a745' if rate >= 80 else '#ffc107' if rate >= 60 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, rate
        )
    installment_completion_rate_display.short_description = 'Installment Completion'
    
    def revenue_breakdown(self, obj):
        return format_html(
            '''
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <h4>Revenue Breakdown for {}</h4>
                <table style="width: 100%; margin-top: 10px;">
                    <tr>
                        <td><strong>M-Pesa Revenue:</strong></td>
                        <td>KES {:,.0f}</td>
                    </tr>
                    <tr>
                        <td><strong>Bank Transfer Revenue:</strong></td>
                        <td>KES {:,.0f}</td>
                    </tr>
                    <tr>
                        <td><strong>PayPal Revenue:</strong></td>
                        <td>KES {:,.0f}</td>
                    </tr>
                    <tr style="border-top: 1px solid #ddd; font-weight: bold;">
                        <td><strong>Total Revenue:</strong></td>
                        <td>KES {:,.0f}</td>
                    </tr>
                </table>
                <p style="margin-top: 10px;">
                    <strong>Average Revenue per User:</strong> KES {:,.0f}
                </p>
            </div>
            ''',
            obj.course.title,
            obj.mpesa_revenue, obj.bank_transfer_revenue, obj.paypal_revenue,
            obj.total_revenue, obj.average_revenue_per_user
        )
    revenue_breakdown.short_description = 'Revenue Breakdown'
