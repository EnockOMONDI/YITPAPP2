from django.contrib import admin
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django import forms
from .models import SponsorshipRequest, OTPVerification, Profile


# Status Update Form for Admin Actions
class StatusUpdateForm(forms.Form):
    """Form for bulk status updates with admin notes"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    new_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label="New Status",
        help_text="Select the new status for selected requests"
    )
    admin_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}),
        required=False,
        label="Admin Notes",
        help_text="Optional notes that will be included in user notification emails"
    )
    send_notification = forms.BooleanField(
        initial=True,
        required=False,
        label="Send Email Notification",
        help_text="Send automatic email notification to users about status change"
    )


def send_status_notification_email(sponsorship_request, admin_user, admin_notes=None):
    """Send status change notification email to user"""
    user = sponsorship_request.user
    status = sponsorship_request.status

    # Determine email template based on status
    template_map = {
        'approved': 'emails/sponsorship_approved',
        'rejected': 'emails/sponsorship_rejected',
        'under_review': 'emails/sponsorship_under_review',
        'pending': 'emails/sponsorship_pending'
    }

    template_base = template_map.get(status, 'emails/sponsorship_status_update')

    # Email context
    context = {
        'user': user,
        'sponsorship_request': sponsorship_request,
        'admin_user': admin_user,
        'admin_notes': admin_notes,
        'status_display': sponsorship_request.get_status_display(),
    }

    # Subject line based on status
    subject_map = {
        'approved': f'✅ Sponsorship Request Approved - {sponsorship_request.get_program_name()}',
        'rejected': f'❌ Sponsorship Request Update - {sponsorship_request.get_program_name()}',
        'under_review': f'🔍 Sponsorship Request Under Review - {sponsorship_request.get_program_name()}',
        'pending': f'📋 Sponsorship Request Status Update - {sponsorship_request.get_program_name()}'
    }

    subject = subject_map.get(status, f'Sponsorship Request Status Update - {sponsorship_request.get_program_name()}')

    try:
        # Render email templates
        html_content = render_to_string(f'{template_base}.html', context)
        text_content = render_to_string(f'{template_base}.txt', context)

        # Create and send email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        return True
    except Exception as e:
        # Log error but don't fail the admin action
        print(f"Failed to send email notification: {e}")
        return False


# Register your models here.
@admin.register(SponsorshipRequest)
class SponsorshipRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_info', 'program_display', 'amount_needed',
        'status_badge', 'priority_indicator', 'days_pending', 'view_full_request', 'quick_actions', 'reviewed_at'
    ]
    list_display_links = ['id', 'user_info', 'program_display']  # Make these columns clickable
    list_filter = [
        'status', 'program', 'financial_situation', 'created_at', 'reviewed_at'
    ]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'reason']
    readonly_fields = [
        'user', 'program', 'program_other', 'amount_needed', 'financial_situation',
        'financial_situation_other', 'reason', 'supporting_document',
        'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_email',
        'emergency_contact_relationship', 'created_at', 'updated_at', 'status_history_display'
    ]
    ordering = ['-created_at']
    list_per_page = 25

    # Enhanced admin interface settings
    save_on_top = True  # Add save buttons at the top of the form
    list_select_related = ['user', 'reviewed_by']  # Optimize database queries

    # Bulk Actions
    actions = [
        'bulk_approve_requests',
        'bulk_reject_requests',
        'bulk_set_under_review',
        'bulk_set_pending',
        'export_selected_requests'
    ]

    fieldsets = (
        ('🔒 Status Management (Editable)', {
            'fields': ('status', 'admin_notes'),
            'description': 'Only these fields can be modified by administrators',
            'classes': ('wide',)
        }),
        ('📋 Request Overview (Read-Only)', {
            'fields': ('user', 'created_at', 'updated_at'),
            'description': 'Basic request information - view only',
            'classes': ('wide',)
        }),
        ('🎓 Program & Financial Details (Read-Only)', {
            'fields': (
                ('program', 'program_other'),
                'amount_needed',
                ('financial_situation', 'financial_situation_other'),
                'reason'
            ),
            'description': 'Program selection, funding amount, and financial circumstances - view only',
            'classes': ('wide',)
        }),
        ('📄 Supporting Documentation (Read-Only)', {
            'fields': ('supporting_document',),
            'description': 'Uploaded supporting documents and verification materials - view only',
            'classes': ('collapse',)
        }),
        ('🚨 Emergency Contact Information (Read-Only)', {
            'fields': (
                ('emergency_contact_name', 'emergency_contact_relationship'),
                ('emergency_contact_phone', 'emergency_contact_email')
            ),
            'description': 'Emergency contact details provided by the applicant - view only',
            'classes': ('collapse',)
        }),
        ('👨‍💼 Administrative Review History (Read-Only)', {
            'fields': ('reviewed_by', 'reviewed_at'),
            'description': 'Review status and administrator information - view only',
            'classes': ('wide',)
        }),
        ('📊 Status History & Audit Trail (Read-Only)', {
            'fields': ('status_history_display',),
            'description': 'Complete timeline of status changes and review history - view only',
            'classes': ('collapse',)
        }),
    )

    def user_info(self, obj):
        """Display comprehensive user information with link to user admin"""
        user_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        full_name = obj.user.get_full_name()
        username = obj.user.username
        email = obj.user.email

        # Build user display with available information
        display_name = full_name if full_name else username

        return format_html(
            '<a href="{}" style="font-weight: bold; color: #0073aa; text-decoration: none;">{}</a><br>'
            '<small style="color: #666;">👤 {}</small><br>'
            '<small style="color: #666;">📧 {}</small>',
            user_url,
            display_name,
            username if full_name else 'Username: ' + username,
            email
        )
    user_info.short_description = 'Applicant'
    user_info.admin_order_field = 'user__username'

    def program_display(self, obj):
        """Display program name"""
        return obj.get_program_name()
    program_display.short_description = 'Program'
    program_display.admin_order_field = 'program'

    def financial_situation_display(self, obj):
        """Display financial situation"""
        return obj.get_financial_situation_name()
    financial_situation_display.short_description = 'Financial Situation'
    financial_situation_display.admin_order_field = 'financial_situation'

    def status_badge(self, obj):
        """Display status with color coding and icons"""
        colors = {
            'pending': '#6c757d',
            'under_review': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
        }
        icons = {
            'pending': '⏳',
            'under_review': '🔍',
            'approved': '✅',
            'rejected': '❌',
        }
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, '📋')
        return format_html(
            '<span style="background: {}; color: white; padding: 6px 10px; border-radius: 6px; font-size: 12px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def priority_indicator(self, obj):
        """Display priority based on amount and days pending"""
        days_old = (timezone.now() - obj.created_at).days
        amount = float(obj.amount_needed)

        # High priority: >$5000 or >14 days old
        if amount > 5000 or days_old > 14:
            return format_html('<span style="color: #dc3545; font-weight: bold;">🔴 High</span>')
        # Medium priority: >$2000 or >7 days old
        elif amount > 2000 or days_old > 7:
            return format_html('<span style="color: #ffc107; font-weight: bold;">🟡 Medium</span>')
        else:
            return format_html('<span style="color: #28a745;">🟢 Normal</span>')
    priority_indicator.short_description = 'Priority'

    def days_pending(self, obj):
        """Display days since submission"""
        days = (timezone.now() - obj.created_at).days
        if days == 0:
            return "Today"
        elif days == 1:
            return "1 day"
        else:
            color = '#dc3545' if days > 14 else '#ffc107' if days > 7 else '#28a745'
            return format_html('<span style="color: {};">{} days</span>', color, days)
    days_pending.short_description = 'Days Pending'

    def view_full_request(self, obj):
        """Display a prominent 'View Full Request' button"""
        view_url = reverse('admin:sponsorship_request_detail_view', args=[obj.pk])
        return format_html(
            '<a href="{}" target="_blank" style="background: linear-gradient(135deg, #341C67 0%, #ff5d15 100%); color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: bold; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
            '📄 View Full Request</a>',
            view_url
        )
    view_full_request.short_description = 'Detailed View'
    view_full_request.allow_tags = True

    def quick_actions(self, obj):
        """Display quick action buttons"""
        change_url = reverse('admin:users_sponsorshiprequest_change', args=[obj.pk])

        if obj.status == 'pending':
            return format_html(
                '<a href="{}?quick_action=approve" onclick="return confirm(\'Approve this sponsorship request?\')" style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-right: 3px;">✓ Approve</a>'
                '<a href="{}?quick_action=review" onclick="return confirm(\'Set this request to under review?\')" style="background: #ffc107; color: black; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-right: 3px;">👁 Review</a>'
                '<a href="{}?quick_action=reject" onclick="return confirm(\'Reject this sponsorship request?\')" style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px;">✗ Reject</a>',
                change_url, change_url, change_url
            )
        elif obj.status == 'under_review':
            return format_html(
                '<a href="{}?quick_action=approve" onclick="return confirm(\'Approve this sponsorship request?\')" style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px; margin-right: 3px;">✓ Approve</a>'
                '<a href="{}?quick_action=reject" onclick="return confirm(\'Reject this sponsorship request?\')" style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px; text-decoration: none; font-size: 11px;">✗ Reject</a>',
                change_url, change_url
            )
        else:
            return format_html('<span style="color: #6c757d; font-size: 11px;">No actions</span>')
    quick_actions.short_description = 'Quick Actions'

    def status_history_display(self, obj):
        """Display status change history"""
        history = []
        history.append(f"Created: {obj.created_at.strftime('%Y-%m-%d %H:%M')}")
        if obj.reviewed_at:
            history.append(f"Reviewed: {obj.reviewed_at.strftime('%Y-%m-%d %H:%M')}")
            if obj.reviewed_by:
                history.append(f"Reviewed by: {obj.reviewed_by.get_full_name() or obj.reviewed_by.username}")
        return format_html('<br>'.join(history))
    status_history_display.short_description = 'Status History'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user', 'reviewed_by')

    def get_urls(self):
        """Add custom URLs for the detailed view"""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:object_id>/detail-view/',
                self.admin_site.admin_view(self.sponsorship_detail_view),
                name='sponsorship_request_detail_view',
            ),
        ]
        return custom_urls + urls

    def sponsorship_detail_view(self, request, object_id):
        """Custom detailed view for sponsorship requests"""
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404("Sponsorship request not found")

        context = {
            'title': f'Sponsorship Request #{obj.id} - Detailed View',
            'sponsorship_request': obj,
            'opts': self.model._meta,
            'has_view_permission': True,
        }

        return render(request, 'admin/sponsorship_request_detail.html', context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Handle quick actions in change view"""
        quick_action = request.GET.get('quick_action')

        if quick_action and object_id:
            try:
                obj = self.get_object(request, object_id)
                if obj:
                    old_status = obj.status

                    # Map quick actions to status
                    action_status_map = {
                        'approve': 'approved',
                        'reject': 'rejected',
                        'review': 'under_review',
                        'pending': 'pending'
                    }

                    new_status = action_status_map.get(quick_action)
                    if new_status and new_status != old_status:
                        obj.status = new_status
                        obj.reviewed_by = request.user
                        obj.reviewed_at = timezone.now()
                        obj.save()

                        # Send notification email
                        send_status_notification_email(obj, request.user)

                        messages.success(
                            request,
                            f'Status updated to "{obj.get_status_display()}" and notification email sent to {obj.user.email}'
                        )

                        # Redirect back to changelist
                        return HttpResponseRedirect(reverse('admin:users_sponsorshiprequest_changelist'))

            except Exception as e:
                messages.error(request, f'Error processing quick action: {str(e)}')

        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        """Enhanced save with status tracking and notifications"""
        old_status = None
        if change:
            # Get the old status before saving
            old_obj = SponsorshipRequest.objects.get(pk=obj.pk)
            old_status = old_obj.status

            # Update review information when status changes
            if 'status' in form.changed_data:
                if obj.status in ['approved', 'rejected', 'under_review']:
                    obj.reviewed_by = request.user
                    obj.reviewed_at = timezone.now()

                    # Send notification email if status changed
                    if old_status != obj.status:
                        super().save_model(request, obj, form, change)
                        send_status_notification_email(obj, request.user)
                        messages.success(
                            request,
                            f'Status updated to "{obj.get_status_display()}" and notification email sent to {obj.user.email}'
                        )
                        return

        super().save_model(request, obj, form, change)

    # Bulk Action Methods
    def bulk_approve_requests(self, request, queryset):
        """Bulk approve selected sponsorship requests"""
        return self._bulk_status_update(request, queryset, 'approved', 'Approved')
    bulk_approve_requests.short_description = "✅ Approve selected requests"

    def bulk_reject_requests(self, request, queryset):
        """Bulk reject selected sponsorship requests"""
        return self._bulk_status_update(request, queryset, 'rejected', 'Rejected')
    bulk_reject_requests.short_description = "❌ Reject selected requests"

    def bulk_set_under_review(self, request, queryset):
        """Bulk set selected requests to under review"""
        return self._bulk_status_update(request, queryset, 'under_review', 'Under Review')
    bulk_set_under_review.short_description = "🔍 Set to Under Review"

    def bulk_set_pending(self, request, queryset):
        """Bulk set selected requests to pending"""
        return self._bulk_status_update(request, queryset, 'pending', 'Pending')
    bulk_set_pending.short_description = "⏳ Set to Pending"

    def _bulk_status_update(self, request, queryset, new_status, status_display):
        """Helper method for bulk status updates"""
        if request.POST.get('post'):
            # Process the form submission
            form = StatusUpdateForm(request.POST)
            if form.is_valid():
                admin_notes = form.cleaned_data['admin_notes']
                send_notification = form.cleaned_data['send_notification']

                updated_count = 0
                email_count = 0

                for obj in queryset:
                    old_status = obj.status
                    obj.status = new_status
                    obj.reviewed_by = request.user
                    obj.reviewed_at = timezone.now()

                    if admin_notes:
                        obj.admin_notes = admin_notes

                    obj.save()
                    updated_count += 1

                    # Send notification email if requested
                    if send_notification and old_status != new_status:
                        if send_status_notification_email(obj, request.user, admin_notes):
                            email_count += 1

                messages.success(
                    request,
                    f'Successfully updated {updated_count} requests to "{status_display}". '
                    f'Sent {email_count} notification emails.'
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            # Show the form
            form = StatusUpdateForm(initial={'new_status': new_status})

        context = {
            'title': f'Bulk Update Status to "{status_display}"',
            'form': form,
            'queryset': queryset,
            'action_checkbox_name': ACTION_CHECKBOX_NAME,
            'new_status': status_display,
            'opts': self.model._meta,
        }

        return render(request, 'admin/bulk_status_update.html', context)

    def export_selected_requests(self, request, queryset):
        """Export selected requests to CSV"""
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sponsorship_requests.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'ID', 'User', 'Email', 'Program', 'Amount', 'Status',
            'Financial Situation', 'Submitted', 'Reviewed', 'Reviewer'
        ])

        for obj in queryset:
            writer.writerow([
                obj.id,
                obj.user.get_full_name() or obj.user.username,
                obj.user.email,
                obj.get_program_name(),
                obj.amount_needed,
                obj.get_status_display(),
                obj.get_financial_situation_name(),
                obj.created_at.strftime('%Y-%m-%d %H:%M'),
                obj.reviewed_at.strftime('%Y-%m-%d %H:%M') if obj.reviewed_at else '',
                obj.reviewed_by.get_full_name() if obj.reviewed_by else ''
            ])

        return response
    export_selected_requests.short_description = "📊 Export selected requests to CSV"


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp_code', 'created_at', 'expires_at', 'is_verified', 'is_used', 'is_expired_status']
    list_filter = ['is_verified', 'is_used', 'created_at']
    search_fields = ['user__username', 'user__email', 'otp_code']
    readonly_fields = ['user', 'otp_code', 'created_at', 'expires_at']
    ordering = ['-created_at']
    list_per_page = 50

    def is_expired_status(self, obj):
        """Display if OTP is expired"""
        if obj.is_expired():
            return format_html('<span style="color: #dc3545;">❌ Expired</span>')
        else:
            return format_html('<span style="color: #28a745;">✅ Valid</span>')
    is_expired_status.short_description = 'Status'

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        return super().get_queryset(request).select_related('user')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user_info', 'email_verification_status', 'location_display_admin',
        'payment_status_badge', 'profile_completion_display', 'last_activity'
    ]
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'phone_number', 'payment_reference', 'country', 'city'
    ]
    list_filter = [
        'email_verified', 'country', 'location_source', 'payment_status',
        'payment_method', 'reminder_emails_stopped', 'user__date_joined'
    ]
    ordering = ['-user__date_joined']
    readonly_fields = [
        'payment_confirmed_at', 'verification_reminder_count', 'last_reminder_sent',
        'profile_completion_percentage', 'created_at', 'updated_at'
    ]
    list_per_page = 50

    actions = [
        'verify_email_status', 'update_location_from_phone', 'confirm_payment',
        'mark_payment_pending', 'mark_payment_expired', 'send_verification_reminder'
    ]

    fieldsets = (
        ('👤 User Information', {
            'fields': ('user', 'phone_number', 'bio', 'image'),
            'classes': ('wide',)
        }),
        ('✅ Email Verification', {
            'fields': (
                'email_verified', 'verification_reminder_count',
                'last_reminder_sent', 'reminder_emails_stopped'
            ),
            'classes': ('wide',)
        }),
        ('🌍 Geographic Location', {
            'fields': (
                'country', 'city', 'timezone_name',
                'ip_address', 'location_source'
            ),
            'classes': ('wide',)
        }),
        ('💳 Payment Information', {
            'fields': (
                'payment_status', 'payment_amount', 'payment_method',
                'payment_reference', 'payment_confirmed_at', 'payment_notes'
            ),
            'classes': ('collapse',)
        }),
        ('📊 Profile Analytics', {
            'fields': (
                'profile_completion_percentage', 'total_points',
                'current_streak', 'longest_streak', 'last_activity_date'
            ),
            'classes': ('collapse',)
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_info(self, obj):
        """Display comprehensive user information with verification status"""
        user_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        full_name = obj.user.get_full_name()
        username = obj.user.username
        email = obj.user.email

        # Build user display with available information
        display_name = full_name if full_name else username

        # Verification badge
        verification_badge = '✅' if obj.email_verified else '❌'

        return format_html(
            '<a href="{}" style="font-weight: bold; color: #0073aa; text-decoration: none;">{}</a> {}<br>'
            '<small style="color: #666;">👤 {}</small><br>'
            '<small style="color: #666;">📧 {}</small>',
            user_url,
            display_name,
            verification_badge,
            username if full_name else 'Username: ' + username,
            email
        )
    user_info.short_description = 'User Information'
    user_info.admin_order_field = 'user__username'

    def email_verification_status(self, obj):
        """Display email verification status with color coding"""
        if obj.email_verified:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">✅ Verified</span>'
            )
        else:
            reminder_info = f" ({obj.verification_reminder_count} reminders)" if obj.verification_reminder_count > 0 else ""
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">❌ Unverified{}</span>',
                reminder_info
            )
    email_verification_status.short_description = 'Email Status'
    email_verification_status.admin_order_field = 'email_verified'

    def location_display_admin(self, obj):
        """Display location information in admin"""
        if obj.country:
            location_text = obj.location_display
            source_icon = {
                'phone': '📱',
                'ip': '🌐',
                'manual': '✏️',
                'unknown': '❓'
            }.get(obj.location_source, '❓')

            return format_html(
                '<span style="color: #0073aa;">{} {}</span><br>'
                '<small style="color: #666;">{} Source: {}</small>',
                source_icon,
                location_text,
                source_icon,
                obj.get_location_source_display()
            )
        else:
            return format_html('<span style="color: #dc3545; font-style: italic;">Location not set</span>')
    location_display_admin.short_description = 'Location'
    location_display_admin.admin_order_field = 'country'

    def payment_status_badge(self, obj):
        """Display payment status with color coding"""
        colors = {
            'unpaid': '#6c757d',
            'pending': '#ffc107',
            'confirmed': '#28a745',
            'expired': '#dc3545',
            'partially_paid': '#17a2b8',
            'sponsorship': '#6f42c1',
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment Status'
    payment_status_badge.admin_order_field = 'payment_status'

    def profile_completion_display(self, obj):
        """Display profile completion percentage with progress bar"""
        percentage = obj.profile_completion_percentage
        color = '#28a745' if percentage >= 80 else '#ffc107' if percentage >= 50 else '#dc3545'

        return format_html(
            '<div style="width: 100px; background: #e9ecef; border-radius: 4px; overflow: hidden;">'
            '<div style="width: {}%; background: {}; height: 20px; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; font-weight: bold;">'
            '{}%</div></div>',
            percentage,
            color,
            int(percentage)
        )
    profile_completion_display.short_description = 'Completion'
    profile_completion_display.admin_order_field = 'profile_completion_percentage'

    def last_activity(self, obj):
        """Display last login activity"""
        if obj.user.last_login:
            from django.utils import timezone
            now = timezone.now()
            diff = now - obj.user.last_login

            if diff.days == 0:
                return format_html('<span style="color: #28a745;">Today</span>')
            elif diff.days == 1:
                return format_html('<span style="color: #ffc107;">Yesterday</span>')
            elif diff.days <= 7:
                return format_html('<span style="color: #ffc107;">{} days ago</span>', diff.days)
            else:
                return format_html('<span style="color: #dc3545;">{} days ago</span>', diff.days)
        else:
            return format_html('<span style="color: #6c757d;">Never</span>')
    last_activity.short_description = 'Last Login'
    last_activity.admin_order_field = 'user__last_login'

    def verification_reminder_status(self, obj):
        """Display verification reminder status"""
        if obj.email_verified:
            return format_html('<span style="color: #28a745;">✅ Verified</span>')

        if obj.reminder_emails_stopped:
            return format_html('<span style="color: #dc3545;">🛑 Stopped ({} sent)</span>', obj.verification_reminder_count)

        if obj.verification_reminder_count > 0:
            return format_html('<span style="color: #ffc107;">📧 {} reminders sent</span>', obj.verification_reminder_count)

        # Check if user needs verification
        if not obj.user.is_active or not obj.email_verified:
            return format_html('<span style="color: #dc3545;">⚠️ Needs verification</span>')

        return format_html('<span style="color: #6c757d;">-</span>')

    verification_reminder_status.short_description = 'Reminder Status'

    def confirm_payment(self, request, queryset):
        """Admin action to confirm payment for selected profiles"""
        updated = 0
        for profile in queryset:
            if profile.payment_status != 'confirmed':
                profile.payment_status = 'confirmed'
                profile.payment_confirmed_at = timezone.now()
                profile.save(update_fields=['payment_status', 'payment_confirmed_at'])
                updated += 1

        self.message_user(
            request,
            f'Successfully confirmed payment for {updated} profile(s).',
            messages.SUCCESS
        )
    confirm_payment.short_description = "Confirm payment for selected profiles"

    def mark_payment_pending(self, request, queryset):
        """Admin action to mark payment as pending for selected profiles"""
        updated = queryset.update(payment_status='pending')
        self.message_user(
            request,
            f'Successfully marked {updated} profile(s) as payment pending.',
            messages.SUCCESS
        )
    mark_payment_pending.short_description = "Mark payment as pending"

    def mark_payment_expired(self, request, queryset):
        """Admin action to mark payment as expired for selected profiles"""
        updated = queryset.update(payment_status='expired')
        self.message_user(
            request,
            f'Successfully marked {updated} profile(s) as payment expired.',
            messages.SUCCESS
        )
    mark_payment_expired.short_description = "Mark payment as expired"

    def send_verification_reminder(self, request, queryset):
        """Admin action to send verification reminder to selected unverified profiles"""
        from users.email_utils import send_verification_reminder_email, generate_otp
        from users.models import OTPVerification
        from datetime import timedelta
        from django.utils import timezone

        sent_count = 0
        failed_count = 0

        for profile in queryset:
            # Only send to unverified users
            if profile.email_verified:
                continue

            user = profile.user

            # Get or create OTP
            current_time = timezone.now()
            valid_otp = OTPVerification.objects.filter(
                user=user,
                is_used=False,
                is_verified=False,
                expires_at__gt=current_time
            ).order_by('-created_at').first()

            if not valid_otp:
                # Create new OTP
                otp_code = generate_otp(length=6)
                expires_at = current_time + timedelta(minutes=200)

                OTPVerification.objects.create(
                    user=user,
                    otp_code=otp_code,
                    expires_at=expires_at
                )
            else:
                otp_code = valid_otp.otp_code

            # Send reminder
            reminder_count = profile.verification_reminder_count + 1
            email_sent = send_verification_reminder_email(
                user=user,
                otp_code=otp_code,
                reminder_count=reminder_count
            )

            if email_sent:
                profile.record_reminder_sent()
                sent_count += 1
            else:
                failed_count += 1

        if sent_count > 0:
            self.message_user(
                request,
                f'Successfully sent verification reminders to {sent_count} user(s).',
                messages.SUCCESS
            )

        if failed_count > 0:
            self.message_user(
                request,
                f'Failed to send reminders to {failed_count} user(s).',
                messages.ERROR
            )

    send_verification_reminder.short_description = "Send verification reminder to unverified users"

    def verify_email_status(self, request, queryset):
        """Admin action to manually verify email status for selected profiles"""
        updated = queryset.update(email_verified=True)
        self.message_user(
            request,
            f'Successfully verified email status for {updated} profile(s).',
            messages.SUCCESS
        )
    verify_email_status.short_description = "✅ Verify email status for selected profiles"

    def update_location_from_phone(self, request, queryset):
        """Admin action to update location information from phone numbers"""
        updated_count = 0
        for profile in queryset:
            if profile.detect_and_update_location():
                updated_count += 1

        self.message_user(
            request,
            f'Successfully updated location for {updated_count} profile(s).',
            messages.SUCCESS
        )
    update_location_from_phone.short_description = "🌍 Update location from phone numbers"

# Non-sponsorship models are intentionally not registered to keep admin focused on sponsorship management
# If you need to manage these models, uncomment the lines below:
# admin.site.register(Profile)
# admin.site.register(Editpage, EditpageAdmin)
# admin.site.register(SecondSection)
# admin.site.register(SecondSectionIcon)
# admin.site.register(SecondSectionBox)

# ============================================================================
# INSTRUCTOR ROLE SYSTEM ADMIN CONFIGURATIONS
# ============================================================================

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import InstructorProfile, Specialization, CourseInstructor


# ============================================================================
# ENHANCED USER ADMIN WITH INSTRUCTOR PROFILE INTEGRATION
# ============================================================================

class InstructorProfileInline(admin.StackedInline):
    """
    Enhanced inline for instructor profiles with visual role indicators
    """
    model = InstructorProfile
    fk_name = 'user'  # Specify which foreign key to use
    can_delete = False
    verbose_name_plural = 'Instructor Profile'
    extra = 0

    fieldsets = (
        ('Role & Verification', {
            'fields': ('instructor_role', 'verification_status'),
            'classes': ('wide',)
        }),
        ('Professional Information', {
            'fields': ('bio', 'qualifications', 'specializations', 'years_experience'),
            'classes': ('collapse',)
        }),
        ('Contact & Social', {
            'fields': ('linkedin_url', 'website_url', 'office_hours'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'can_create_courses',
                'can_manage_assessments', 'can_view_analytics'
            ),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = ['specializations']
    readonly_fields = ['verified_at', 'verified_by']

    def get_readonly_fields(self, request, obj=None):
        """Make verification fields readonly for non-superusers"""
        readonly = list(self.readonly_fields)
        if not request.user.is_superuser:
            readonly.extend(['verification_status'])
        return readonly


class ProfileInline(admin.StackedInline):
    """
    Inline for Profile information in User admin
    """
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile Information'
    extra = 0

    fieldsets = (
        ('Email Verification', {
            'fields': ('email_verified', 'verification_reminder_count'),
            'classes': ('wide',)
        }),
        ('Location Information', {
            'fields': ('country', 'city', 'location_source'),
            'classes': ('wide',)
        }),
        ('Payment Status', {
            'fields': ('payment_status', 'payment_method'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['verification_reminder_count']


class CustomUserAdmin(BaseUserAdmin):
    """
    Enhanced User admin with profile and instructor profile integration
    """
    inlines = (ProfileInline, InstructorProfileInline)

    # Override add_fieldsets to include email field in user creation form
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "first_name", "last_name", "password1", "password2"),
            },
        ),
    )

    def get_list_display(self, request):
        """Enhanced list display with profile and instructor information"""
        base_display = list(super().get_list_display(request))
        # Insert profile information after username
        if 'username' in base_display:
            username_index = base_display.index('username')
            base_display.insert(username_index + 1, 'email_verification_display')
            base_display.insert(username_index + 2, 'location_info_display')
            base_display.insert(username_index + 3, 'instructor_role_display')
            base_display.insert(username_index + 4, 'verification_status_display')
        return base_display

    def email_verification_display(self, obj):
        """Display email verification status from profile"""
        if hasattr(obj, 'profile'):
            if obj.profile.email_verified:
                return format_html('<span style="color: #28a745; font-weight: bold;">✅</span>')
            else:
                return format_html('<span style="color: #dc3545; font-weight: bold;">❌</span>')
        return format_html('<span style="color: #6c757d;">-</span>')
    email_verification_display.short_description = 'Email Verified'
    email_verification_display.admin_order_field = 'profile__email_verified'

    def location_info_display(self, obj):
        """Display location information from profile"""
        if hasattr(obj, 'profile') and obj.profile.country:
            return format_html(
                '<span style="color: #0073aa; font-size: 11px;">{}</span>',
                obj.profile.country
            )
        return format_html('<span style="color: #6c757d; font-size: 11px;">-</span>')
    location_info_display.short_description = 'Location'
    location_info_display.admin_order_field = 'profile__country'

    def instructor_role_display(self, obj):
        """Display instructor role with color coding"""
        if hasattr(obj, 'instructor_profile'):
            profile = obj.instructor_profile
            role_colors = {
                'system_admin': '#dc3545',  # Red
                'course_instructor': '#ff5d15',  # YITP Orange
                'teaching_assistant': '#28a745',  # Green
                'content_creator': '#17a2b8',  # Cyan
                'grader': '#6c757d',  # Gray
            }
            color = role_colors.get(profile.instructor_role, '#6c757d')
            return format_html(
                '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
                color,
                profile.get_instructor_role_display()
            )
        return format_html('<span style="color: #6c757d; font-style: italic;">Student</span>')
    instructor_role_display.short_description = 'Role'
    instructor_role_display.admin_order_field = 'instructor_profile__instructor_role'

    def verification_status_display(self, obj):
        """Display verification status with color coding"""
        if hasattr(obj, 'instructor_profile'):
            profile = obj.instructor_profile
            status_colors = {
                'verified': '#28a745',  # Green
                'pending': '#ffc107',  # Yellow
                'rejected': '#dc3545',  # Red
            }
            color = status_colors.get(profile.verification_status, '#6c757d')
            icon = {
                'verified': '✅',
                'pending': '⏳',
                'rejected': '❌',
            }.get(profile.verification_status, '❓')

            return format_html(
                '<span style="color: {}; font-weight: bold;">{} {}</span>',
                color,
                icon,
                profile.get_verification_status_display()
            )
        return '-'
    verification_status_display.short_description = 'Verification'
    verification_status_display.admin_order_field = 'instructor_profile__verification_status'

    def save_model(self, request, obj, form, change):
        """Enhanced save with auto-verification and email notification for instructor profiles"""
        is_new_user = not change
        super().save_model(request, obj, form, change)

        # Handle instructor profile creation and verification
        if hasattr(obj, 'instructor_profile'):
            profile = obj.instructor_profile

            # Auto-verify instructor profiles created by superusers
            if request.user.is_superuser and profile.verification_status == 'pending':
                profile.verification_status = 'verified'
                profile.verified_at = timezone.now()
                profile.verified_by = request.user
                profile.save()

                messages.success(
                    request,
                    f'Instructor profile for {obj.get_full_name() or obj.username} has been automatically verified.'
                )

            # Send welcome email for newly created users with instructor profiles
            if is_new_user:
                try:
                    from .email_utils import send_instructor_welcome_email, log_instructor_account_creation

                    # Validate email address before sending
                    if not obj.email or not obj.email.strip():
                        messages.warning(
                            request,
                            f'Instructor account created successfully, but no email address provided. '
                            'Please add an email address and manually send welcome instructions.'
                        )
                        return

                    # Send welcome email
                    email_sent = send_instructor_welcome_email(
                        user=obj,
                        instructor_profile=profile,
                        temporary_password=None,  # Admin-created accounts use admin-set passwords
                        created_by_admin=request.user
                    )

                    # Log the account creation
                    log_instructor_account_creation(
                        user=obj,
                        instructor_profile=profile,
                        created_by_admin=request.user,
                        email_sent=email_sent
                    )

                    if email_sent:
                        messages.success(
                            request,
                            f'Welcome email sent to {obj.email} with instructor account details and login instructions.'
                        )
                    else:
                        messages.warning(
                            request,
                            f'User created successfully, but failed to send welcome email to {obj.email}. '
                            'Please manually provide login credentials to the instructor.'
                        )

                except Exception as e:
                    messages.error(
                        request,
                        f'User created successfully, but email notification failed: {str(e)}'
                    )

    def get_queryset(self, request):
        """Optimize queries with select_related for profiles and instructor profiles"""
        return super().get_queryset(request).select_related('profile', 'instructor_profile')


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    """Admin interface for instructor specializations"""
    list_display = ['name', 'slug', 'color', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'color', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    """Enhanced admin interface for instructor profiles with visual indicators"""
    list_display = [
        'user_full_name', 'instructor_role_display', 'verification_status_display',
        'years_experience', 'specializations_count', 'is_active', 'created_at'
    ]
    list_filter = [
        'instructor_role', 'verification_status', 'is_active',
        'can_create_courses', 'can_manage_assessments', 'can_view_analytics',
        'created_at', 'specializations'
    ]
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'user__email', 'bio', 'qualifications'
    ]
    readonly_fields = ['created_at', 'updated_at', 'verified_at']
    filter_horizontal = ['specializations']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'instructor_role', 'verification_status')
        }),
        ('Professional Information', {
            'fields': ('bio', 'qualifications', 'specializations', 'years_experience')
        }),
        ('Contact & Social', {
            'fields': ('linkedin_url', 'website_url', 'office_hours'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'can_create_courses',
                'can_manage_assessments', 'can_view_analytics'
            )
        }),
        ('Verification', {
            'fields': ('verified_at', 'verified_by'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['verify_instructors', 'deactivate_instructors', 'activate_instructors']

    def user_full_name(self, obj):
        """Display user's full name with link to user admin"""
        user_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html(
            '<a href="{}" style="color: #ff5d15; font-weight: bold;">{}</a>',
            user_url,
            obj.user.get_full_name() or obj.user.username
        )
    user_full_name.short_description = 'Instructor Name'
    user_full_name.admin_order_field = 'user__first_name'

    def instructor_role_display(self, obj):
        """Display instructor role with color coding"""
        role_colors = {
            'system_admin': '#dc3545',  # Red
            'course_instructor': '#ff5d15',  # YITP Orange
            'teaching_assistant': '#28a745',  # Green
            'content_creator': '#17a2b8',  # Cyan
            'grader': '#6c757d',  # Gray
        }
        color = role_colors.get(obj.instructor_role, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_instructor_role_display()
        )
    instructor_role_display.short_description = 'Role'
    instructor_role_display.admin_order_field = 'instructor_role'

    def verification_status_display(self, obj):
        """Display verification status with color coding"""
        status_colors = {
            'verified': '#28a745',  # Green
            'pending': '#ffc107',  # Yellow
            'rejected': '#dc3545',  # Red
        }
        color = status_colors.get(obj.verification_status, '#6c757d')
        icon = {
            'verified': '✅',
            'pending': '⏳',
            'rejected': '❌',
        }.get(obj.verification_status, '❓')

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_verification_status_display()
        )
    verification_status_display.short_description = 'Verification'
    verification_status_display.admin_order_field = 'verification_status'

    def specializations_count(self, obj):
        """Display count of specializations"""
        count = obj.specializations.count()
        if count > 0:
            return format_html(
                '<span style="background: #ff5d15; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
                count
            )
        return '-'
    specializations_count.short_description = 'Specializations'

    def save_model(self, request, obj, form, change):
        """Enhanced save with auto-verification and email notification for instructor profiles"""
        # Auto-verify instructor profiles created by superusers
        if request.user.is_superuser and obj.verification_status == 'pending':
            obj.verification_status = 'verified'
            obj.verified_at = timezone.now()
            obj.verified_by = request.user

            messages.success(
                request,
                f'Instructor profile for {obj.user.get_full_name() or obj.user.username} has been automatically verified.'
            )

        super().save_model(request, obj, form, change)

        # Send welcome email for newly created instructor profiles
        if not change:  # Only for new profiles
            try:
                from .email_utils import send_instructor_welcome_email, log_instructor_account_creation

                # Send welcome email
                email_sent = send_instructor_welcome_email(
                    user=obj.user,
                    instructor_profile=obj,
                    temporary_password=None,  # Admin-created accounts use admin-set passwords
                    created_by_admin=request.user
                )

                # Log the account creation
                log_instructor_account_creation(
                    user=obj.user,
                    instructor_profile=obj,
                    created_by_admin=request.user,
                    email_sent=email_sent
                )

                if email_sent:
                    messages.success(
                        request,
                        f'Welcome email sent to {obj.user.email} with account details and login instructions.'
                    )
                else:
                    messages.warning(
                        request,
                        f'Instructor profile created successfully, but failed to send welcome email to {obj.user.email}. '
                        'Please manually provide login credentials to the instructor.'
                    )

            except Exception as e:
                messages.error(
                    request,
                    f'Instructor profile created successfully, but email notification failed: {str(e)}'
                )

    def verify_instructors(self, request, queryset):
        """Bulk action to verify instructors"""
        updated = queryset.update(
            verification_status='verified',
            verified_at=timezone.now(),
            verified_by=request.user
        )
        self.message_user(
            request,
            f'{updated} instructor(s) have been verified.',
            messages.SUCCESS
        )
    verify_instructors.short_description = "Verify selected instructors"

    def deactivate_instructors(self, request, queryset):
        """Bulk action to deactivate instructors"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} instructor(s) have been deactivated.',
            messages.WARNING
        )
    deactivate_instructors.short_description = "Deactivate selected instructors"

    def activate_instructors(self, request, queryset):
        """Bulk action to activate instructors"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} instructor(s) have been activated.',
            messages.SUCCESS
        )
    activate_instructors.short_description = "Activate selected instructors"


@admin.register(CourseInstructor)
class CourseInstructorAdmin(admin.ModelAdmin):
    """Admin interface for course instructor assignments"""
    list_display = [
        'instructor_name', 'course_title', 'assignment_role',
        'permissions_summary', 'is_active', 'assigned_at'
    ]
    list_filter = [
        'assignment_role', 'is_active', 'assigned_at',
        'can_edit_content', 'can_manage_enrollments', 'can_grade_assessments'
    ]
    search_fields = [
        'instructor__username', 'instructor__first_name', 'instructor__last_name',
        'course__title', 'course__slug'
    ]
    readonly_fields = ['assigned_at']

    fieldsets = (
        ('Assignment Details', {
            'fields': ('course', 'instructor', 'assignment_role', 'is_active')
        }),
        ('Permissions', {
            'fields': (
                'can_edit_content', 'can_manage_enrollments',
                'can_grade_assessments', 'can_view_analytics',
                'can_communicate_students', 'can_publish_course'
            )
        }),
        ('Assignment Info', {
            'fields': ('assigned_by', 'assigned_at', 'notes'),
            'classes': ('collapse',)
        }),
    )

    def instructor_name(self, obj):
        """Display instructor name with link"""
        instructor_url = reverse('admin:users_instructorprofile_change',
                               args=[obj.instructor.instructor_profile.pk])
        return format_html(
            '<a href="{}" style="color: #341C67; font-weight: bold;">{}</a>',
            instructor_url,
            obj.instructor.get_full_name() or obj.instructor.username
        )
    instructor_name.short_description = 'Instructor'
    instructor_name.admin_order_field = 'instructor__first_name'

    def course_title(self, obj):
        """Display course title with link"""
        course_url = reverse('admin:courses_course_change', args=[obj.course.pk])
        return format_html(
            '<a href="{}" style="color: #ff5d15; font-weight: bold;">{}</a>',
            course_url,
            obj.course.title
        )
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'course__title'

    def permissions_summary(self, obj):
        """Display permissions summary"""
        permissions = []
        if obj.can_edit_content:
            permissions.append('Edit')
        if obj.can_manage_enrollments:
            permissions.append('Enroll')
        if obj.can_grade_assessments:
            permissions.append('Grade')
        if obj.can_view_analytics:
            permissions.append('Analytics')

        if permissions:
            return format_html(
                '<span style="font-size: 11px; color: #666;">{}</span>',
                ' • '.join(permissions)
            )
        return '-'
    permissions_summary.short_description = 'Permissions'


# Customize admin site headers for better branding
admin.site.site_header = "YITP Learning Management System"
admin.site.site_title = "YITP LMS Admin"
admin.site.index_title = "Youth Impact Training Programme - LMS Administration"