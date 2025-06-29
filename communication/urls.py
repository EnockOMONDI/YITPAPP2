from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    # Messaging URLs
    path('', views.MessageDashboardView.as_view(), name='dashboard'),
    path('inbox/', views.InboxView.as_view(), name='inbox'),
    path('sent/', views.SentMessagesView.as_view(), name='sent'),
    path('compose/', views.ComposeMessageView.as_view(), name='compose'),
    path('message/<int:message_id>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('message/<int:message_id>/reply/', views.ReplyMessageView.as_view(), name='reply_message'),
    
    # Discussion Forums
    path('forums/', views.ForumListView.as_view(), name='forum_list'),
    path('forums/<int:forum_id>/', views.ForumDetailView.as_view(), name='forum_detail'),
    path('forums/<int:forum_id>/new-topic/', views.CreateTopicView.as_view(), name='create_topic'),
    path('topics/<int:topic_id>/', views.TopicDetailView.as_view(), name='topic_detail'),
    path('topics/<int:topic_id>/reply/', views.ReplyTopicView.as_view(), name='reply_topic'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.MarkNotificationReadView.as_view(), name='mark_notification_read'),
    path('notifications/mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_notifications_read'),
    
    # Announcements
    path('announcements/', views.AnnouncementListView.as_view(), name='announcements'),
    path('announcements/<int:announcement_id>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),
    
    # API endpoints for real-time features
    path('api/send-message/', views.SendMessageAPIView.as_view(), name='send_message_api'),
    path('api/get-unread-count/', views.GetUnreadCountAPIView.as_view(), name='get_unread_count'),
]
