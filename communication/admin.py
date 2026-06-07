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
        """Filter messages based on instructor role with prefetching"""
        qs = super().get_queryset(request).select_related(
            'sender__instructor_profile',
            'recipient__instructor_profile'
        )

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
    list_select_related = ['user']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_per_page = 25

@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'course', 'created_by', 'is_moderated', 'is_active', 'created_at']
    list_filter = ['is_moderated', 'is_active', 'course']
    search_fields = ['title', 'description', 'course__title', 'created_by__username']
    list_select_related = ['course', 'created_by']
    list_per_page = 25

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'forum', 'created_by', 'is_pinned', 'is_locked', 'view_count', 'reply_count', 'created_at']
    list_filter = ['is_pinned', 'is_locked', 'forum__course']
    search_fields = ['title', 'content', 'forum__title', 'created_by__username']
    list_select_related = ['forum__course', 'created_by']
    list_per_page = 25

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'created_by', 'parent_reply', 'is_solution', 'like_count', 'created_at']
    list_filter = ['is_solution', 'topic__forum__course']
    search_fields = ['content', 'topic__title', 'created_by__username']
    list_select_related = ['topic__forum__course', 'created_by', 'parent_reply']
    list_per_page = 25

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_type', 'object_id', 'feedback_type', 'rating', 'given_by', 'received_by', 'created_at']
    list_filter = ['feedback_type', 'content_type', 'rating']
    search_fields = ['comment', 'given_by__username', 'received_by__username']
    list_select_related = ['given_by', 'received_by']
    list_per_page = 25

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'course', 'priority', 'is_published', 'publish_date', 'created_by']
    list_filter = ['priority', 'is_published', 'course']
    search_fields = ['title', 'content', 'course__title', 'created_by__username']
    list_select_related = ['course', 'created_by']
    list_per_page = 25

@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'course', 'is_public', 'max_members', 'created_by', 'created_at']
    list_filter = ['is_public', 'course']
    search_fields = ['name', 'description', 'course__title', 'created_by__username']
    list_select_related = ['course', 'created_by']
    list_per_page = 25

@admin.register(StudyGroupMembership)
class StudyGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['id', 'study_group', 'user', 'role', 'joined_at']
    list_filter = ['role', 'study_group__course']
    search_fields = ['study_group__name', 'user__username', 'user__first_name', 'user__last_name']
    list_select_related = ['study_group__course', 'user']
    list_per_page = 25