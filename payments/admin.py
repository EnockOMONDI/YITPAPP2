"""
Django Admin Configuration for Payment Management
Provides admin interface for verifying PayPal and bank transfer payments
"""

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Payment
from .payment_service import PaymentService


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 
        'user_display', 
        'course_display', 
        'amount_display', 
        'payment_method_display', 
        'status_display', 
        'installment_display',
        'created_at'
    ]
    
    list_filter = [
        'status', 
        'payment_method', 
        'is_installment', 
        'installment_sequence',
        'created_at'
    ]
    
    search_fields = [
        'reference_number', 
        'user__username', 
        'user__email', 
        'course__title',
        'paypal_payment_id',
        'transaction_id'
    ]
    
    readonly_fields = [
        'reference_number', 
        'user', 
        'course', 
        'amount', 
        'payment_method',
        'is_installment',
        'installment_sequence',
        'created_at',
        'paypal_payment_id',
        'paypal_payer_id',
        'transaction_id'
    ]
    
    fieldsets = (
        ('Payment Information', {
            'fields': (
                'reference_number',
                'user',
                'course',
                'amount',
                'payment_method',
                'status'
            )
        }),
        ('Installment Details', {
            'fields': (
                'is_installment',
                'installment_sequence'
            ),
            'classes': ('collapse',)
        }),
        ('Transaction Details', {
            'fields': (
                'transaction_id',
                'paypal_payment_id',
                'paypal_payer_id'
            ),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': (
                'verified_by',
                'verification_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['verify_payments', 'reject_payments', 'mark_pending']
    
    def user_display(self, obj):
        """Display user with link to user admin"""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return '-'
    user_display.short_description = 'User'
    
    def course_display(self, obj):
        """Display course with link to course admin"""
        if obj.course:
            try:
                url = reverse('admin:courses_course_change', args=[obj.course.id])
                return format_html('<a href="{}">{}</a>', url, obj.course.title)
            except:
                return obj.course.title
        return '-'
    course_display.short_description = 'Course'
    
    def amount_display(self, obj):
        """Display formatted amount"""
        currency = obj.currency or 'USD'
        return f"${obj.amount:,.2f} {currency}"
    amount_display.short_description = 'Amount'
    
    def payment_method_display(self, obj):
        """Display payment method with icon"""
        icons = {
            'mpesa': '📱',
            'paypal': '💳',
            'bank_transfer': '🏦',
            'card': '💳'
        }
        icon = icons.get(obj.payment_method, '💰')
        return f"{icon} {obj.get_payment_method_display()}"
    payment_method_display.short_description = 'Payment Method'
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'pending': '#ffc107',
            'confirmed': '#28a745',
            'failed': '#dc3545',
            'expired': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def installment_display(self, obj):
        """Display installment information"""
        if obj.is_installment:
            return f"Installment {obj.installment_sequence}/2"
        return "Full Payment"
    installment_display.short_description = 'Payment Type'
    
    def verify_payments(self, request, queryset):
        """Admin action to verify selected payments with email notifications"""
        verified_count = 0
        failed_count = 0

        for payment in queryset.filter(status='pending'):
            try:
                # Use the enhanced confirmation method
                result = PaymentService.confirm_payment_and_enroll(
                    payment=payment,
                    verified_by=request.user
                )

                if result['success']:
                    verified_count += 1

                    # Send verification email to user
                    from .email_service import PaymentEmailService
                    email_sent = PaymentEmailService.send_payment_verified_notification(payment)
                    if not email_sent:
                        messages.warning(request, f"Payment {payment.reference_number} verified but email notification failed.")
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                messages.error(request, f"Failed to verify payment {payment.reference_number}: {str(e)}")

        if verified_count > 0:
            messages.success(request, f"Successfully verified {verified_count} payment(s) and enrolled users in courses. Email notifications sent.")

        if failed_count > 0:
            messages.error(request, f"Failed to verify {failed_count} payment(s).")
    
    verify_payments.short_description = "Verify selected payments and enroll users"
    
    def reject_payments(self, request, queryset):
        """Admin action to reject selected payments with email notifications"""
        rejected_count = 0

        for payment in queryset.filter(status='pending'):
            payment.status = 'failed'
            payment.verified_by = request.user
            payment.verification_notes = f"Rejected by admin: {request.user.username}"
            payment.save()
            rejected_count += 1

            # Send rejection email to user
            from .email_service import PaymentEmailService
            email_sent = PaymentEmailService.send_payment_rejected_notification(
                payment,
                reason="Payment verification failed during admin review."
            )
            if not email_sent:
                messages.warning(request, f"Payment {payment.reference_number} rejected but email notification failed.")

        if rejected_count > 0:
            messages.success(request, f"Successfully rejected {rejected_count} payment(s). Email notifications sent.")
    
    reject_payments.short_description = "Reject selected payments"
    
    def mark_pending(self, request, queryset):
        """Admin action to mark payments as pending for re-verification"""
        pending_count = 0
        
        for payment in queryset.exclude(status='pending'):
            payment.status = 'pending'
            payment.verification_notes = f"Marked pending for re-verification by: {request.user.username}"
            payment.save()
            pending_count += 1
        
        if pending_count > 0:
            messages.success(request, f"Successfully marked {pending_count} payment(s) as pending.")
    
    mark_pending.short_description = "Mark as pending for re-verification"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'course', 'verified_by')
    
    def has_delete_permission(self, request, obj=None):
        """Restrict deletion of confirmed payments"""
        if obj and obj.status == 'confirmed':
            return False
        return super().has_delete_permission(request, obj)


# Register additional admin customizations if needed
admin.site.site_header = "YITP Payment Administration"
admin.site.site_title = "YITP Payments"
admin.site.index_title = "Payment Management Dashboard"
