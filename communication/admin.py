from django.contrib import admin
from .models import (
    Forum, Topic, Reply, Message, Feedback, Announcement,
    Notification, StudyGroup, StudyGroupMembership
)

# Simple admin registrations for immediate functionality
admin.site.register(Forum)
admin.site.register(Topic)
admin.site.register(Reply)
admin.site.register(Message)
admin.site.register(Feedback)
admin.site.register(Announcement)
admin.site.register(Notification)
admin.site.register(StudyGroup)
admin.site.register(StudyGroupMembership)