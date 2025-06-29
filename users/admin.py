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
            '<a href="{}" target="_blank" style="background: linear-gradient(135deg, #0e1133 0%, #ff5d15 100%); color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: bold; display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">'
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
    list_display = ['user', 'phone_number', 'payment_status', 'payment_amount', 'payment_confirmed_at', 'bio_preview']
    search_fields = ['user__username', 'user__email', 'phone_number', 'payment_reference']
    list_filter = ['user__date_joined', 'payment_status', 'payment_method', 'payment_confirmed_at']
    ordering = ['user__username']
    readonly_fields = ['payment_confirmed_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number', 'bio', 'image')
        }),
        ('Payment Information', {
            'fields': (
                'payment_status', 'payment_amount', 'payment_method',
                'payment_reference', 'payment_confirmed_at', 'payment_notes'
            ),
            'classes': ('collapse',)
        }),
    )

    actions = ['confirm_payment', 'mark_payment_pending', 'mark_payment_expired']

    def bio_preview(self, obj):
        """Display truncated bio"""
        if obj.bio and obj.bio != 'Edit your Bio!':
            return obj.bio[:50] + '...' if len(obj.bio) > 50 else obj.bio
        return 'No bio set'
    bio_preview.short_description = 'Bio Preview'

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

# Non-sponsorship models are intentionally not registered to keep admin focused on sponsorship management
# If you need to manage these models, uncomment the lines below:
# admin.site.register(Profile)
# admin.site.register(Editpage, EditpageAdmin)
# admin.site.register(SecondSection)
# admin.site.register(SecondSectionIcon)
# admin.site.register(SecondSectionBox)

# Customize admin site headers for better branding
admin.site.site_header = "YITP Sponsorship Management"
admin.site.site_title = "YITP Admin"
admin.site.index_title = "Youth Impact Training Programme - Sponsorship Request Management"