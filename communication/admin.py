from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import (
    Forum, Topic, Reply, Message, Feedback, Announcement,
    Notification, StudyGroup, StudyGroupMembership
)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Enhanced message admin interface with instructor filtering"""
    list_display = [
        'sender_name', 'recipient_name', 'subject_preview',
        'message_type', 'sent_at', 'read_status'
    ]
    list_filter = [
        'is_read', 'sent_at', 'sender__instructor_profile__instructor_role'
    ]
    search_fields = [
        'sender__username', 'sender__first_name', 'sender__last_name',
        'recipient__username', 'recipient__first_name', 'recipient__last_name',
        'subject', 'content'
    ]
    readonly_fields = ['sent_at', 'read_at']
    ordering = ['-sent_at']

    fieldsets = (
        ('Message Details', {
            'fields': ('sender', 'recipient', 'subject', 'content')
        }),
        ('Thread Information', {
            'fields': ('parent_message',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'is_archived', 'sent_at', 'read_at')
        }),
    )

    actions = ['mark_as_read', 'mark_as_unread', 'archive_messages']

    def get_queryset(self, request):
        """Filter messages based on instructor role"""
        qs = super().get_queryset(request).select_related('sender', 'recipient')

        # System admins see all messages
        if request.user.is_superuser:
            return qs

        # Check if user has instructor profile
        try:
            instructor_profile = request.user.instructor_profile
            if instructor_profile.instructor_role == 'system_admin':
                return qs
            else:
                # Course instructors see only their messages
                return qs.filter(
                    Q(sender=request.user) | Q(recipient=request.user)
                )
        except:
            # Regular staff users see only their messages
            return qs.filter(
                Q(sender=request.user) | Q(recipient=request.user)
            )

    def sender_name(self, obj):
        """Display sender name with role indicator"""
        name = obj.sender.get_full_name() or obj.sender.username

        # Check if sender is instructor
        try:
            instructor_profile = obj.sender.instructor_profile
            role_badge = f'<span style="background: #ff5d15; color: white; padding: 1px 4px; border-radius: 3px; font-size: 10px; margin-left: 5px;">{instructor_profile.get_instructor_role_display()}</span>'
            return format_html('{} {}', name, role_badge)
        except:
            return name
    sender_name.short_description = 'From'
    sender_name.admin_order_field = 'sender__first_name'

    def recipient_name(self, obj):
        """Display recipient name with role indicator"""
        name = obj.recipient.get_full_name() or obj.recipient.username

        # Check if recipient is instructor
        try:
            instructor_profile = obj.recipient.instructor_profile
            role_badge = f'<span style="background: #341C67; color: white; padding: 1px 4px; border-radius: 3px; font-size: 10px; margin-left: 5px;">{instructor_profile.get_instructor_role_display()}</span>'
            return format_html('{} {}', name, role_badge)
        except:
            return name
    recipient_name.short_description = 'To'
    recipient_name.admin_order_field = 'recipient__first_name'

    def subject_preview(self, obj):
        """Display subject with content preview"""
        content_preview = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return format_html(
            '<strong>{}</strong><br><small style="color: #6c757d;">{}</small>',
            obj.subject,
            content_preview
        )
    subject_preview.short_description = 'Subject / Preview'
    subject_preview.admin_order_field = 'subject'

    def message_type(self, obj):
        """Determine and display message type"""
        if obj.parent_message:
            return format_html(
                '<span style="background: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Reply</span>'
            )
        elif "lesson" in obj.subject.lower() or "quiz" in obj.subject.lower():
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Course</span>'
            )
        else:
            return format_html(
                '<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">General</span>'
            )
    message_type.short_description = 'Type'

    def read_status(self, obj):
        """Display read status with styling"""
        if obj.is_read:
            return format_html(
                '<span style="color: #28a745;"><i class="fas fa-check-circle"></i> Read</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545;"><i class="fas fa-circle"></i> Unread</span>'
            )
    read_status.short_description = 'Status'
    read_status.admin_order_field = 'is_read'

    def mark_as_read(self, request, queryset):
        """Bulk action to mark messages as read"""
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(
            request,
            f'{updated} message(s) marked as read.',
            messages.SUCCESS
        )
    mark_as_read.short_description = "Mark selected messages as read"

    def mark_as_unread(self, request, queryset):
        """Bulk action to mark messages as unread"""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(
            request,
            f'{updated} message(s) marked as unread.',
            messages.INFO
        )
    mark_as_unread.short_description = "Mark selected messages as unread"

    def archive_messages(self, request, queryset):
        """Bulk action to archive messages"""
        updated = queryset.update(is_archived=True)
        self.message_user(
            request,
            f'{updated} message(s) archived.',
            messages.WARNING
        )
    archive_messages.short_description = "Archive selected messages"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'created_at', 'is_read']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

# Simple admin registrations for other models
admin.site.register(Forum)
admin.site.register(Topic)
admin.site.register(Reply)
admin.site.register(Feedback)
admin.site.register(Announcement)
admin.site.register(StudyGroup)
admin.site.register(StudyGroupMembership)