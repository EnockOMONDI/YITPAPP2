from django.contrib import admin
from .models import (
    Forum, Topic, Reply, Message, Feedback, Announcement,
    Notification, StudyGroup, StudyGroupMembership
)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'sent_at', 'is_read']
    list_filter = ['is_read', 'sent_at']
    search_fields = ['sender__username', 'recipient__username', 'subject', 'content']
    readonly_fields = ['sent_at']
    ordering = ['-sent_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Show lesson-related messages prominently
        return qs.select_related('sender', 'recipient')

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