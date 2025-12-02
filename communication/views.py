from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView, View, CreateView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from .models import Message, Forum, Topic, Reply, Notification, Announcement

User = get_user_model()


class MessageDashboardView(LoginRequiredMixin, TemplateView):
    """Communication dashboard"""
    template_name = 'lms/communication/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Message statistics
        context['unread_messages'] = Message.objects.filter(
            recipient=user,
            is_read=False
        ).count()

        context['total_messages'] = Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).count()

        # Recent messages
        context['recent_messages'] = Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).order_by('-sent_at')[:5]

        # Unread notifications
        context['unread_notifications'] = Notification.objects.filter(
            user=user,
            is_read=False
        ).count()

        # Recent announcements
        context['recent_announcements'] = Announcement.objects.filter(
            is_published=True
        ).order_by('-created_at')[:3]

        return context


class InboxView(LoginRequiredMixin, ListView):
    """User inbox"""
    template_name = 'lms/communication/inbox.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(
            recipient=self.request.user
        ).order_by('-sent_at')


class SentMessagesView(LoginRequiredMixin, ListView):
    """Sent messages"""
    template_name = 'lms/communication/sent.html'
    context_object_name = 'messages'
    paginate_by = 20

    def get_queryset(self):
        return Message.objects.filter(
            sender=self.request.user
        ).order_by('-sent_at')


class ComposeMessageView(LoginRequiredMixin, CreateView):
    """Compose new message"""
    model = Message
    template_name = 'lms/communication/compose.html'
    fields = ['recipient', 'subject', 'content']

    def form_valid(self, form):
        form.instance.sender = self.request.user
        messages.success(self.request, 'Message sent successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('communication:inbox')


class MessageDetailView(LoginRequiredMixin, DetailView):
    """Message detail view"""
    model = Message
    template_name = 'lms/communication/message_detail.html'
    context_object_name = 'message'
    pk_url_kwarg = 'message_id'

    def get_queryset(self):
        # Only show messages where user is sender or recipient
        return Message.objects.filter(
            Q(sender=self.request.user) | Q(recipient=self.request.user)
        )

    def get_object(self):
        message = super().get_object()
        # Mark as read if user is recipient
        if message.recipient == self.request.user and not message.is_read:
            message.is_read = True
            message.read_at = timezone.now()
            message.save()
        return message


class ReplyMessageView(LoginRequiredMixin, CreateView):
    """Reply to message"""
    model = Message
    template_name = 'lms/communication/reply.html'
    fields = ['content']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        original_message = get_object_or_404(
            Message,
            id=self.kwargs['message_id'],
            recipient=self.request.user
        )
        context['original_message'] = original_message
        return context

    def form_valid(self, form):
        original_message = get_object_or_404(
            Message,
            id=self.kwargs['message_id'],
            recipient=self.request.user
        )

        form.instance.sender = self.request.user
        form.instance.recipient = original_message.sender
        form.instance.subject = f"Re: {original_message.subject}"
        form.instance.parent_message = original_message

        messages.success(self.request, 'Reply sent successfully!')
        return super().form_valid(form)


class ForumListView(ListView):
    """List all forums"""
    model = Forum
    template_name = 'lms/communication/forum_list.html'
    context_object_name = 'forums'

    def get_queryset(self):
        return Forum.objects.filter(is_active=True).select_related('course').order_by('course__title', 'title')


class ForumDetailView(DetailView):
    """Forum detail with topics"""
    model = Forum
    template_name = 'lms/communication/forum_detail.html'
    context_object_name = 'forum'
    pk_url_kwarg = 'forum_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forum = self.object

        # Get topics in this forum
        topics = forum.topics.select_related('forum').order_by('-is_pinned', '-updated_at')

        context['topics'] = topics
        return context


class CreateTopicView(LoginRequiredMixin, CreateView):
    """Create new forum topic"""
    model = Topic
    template_name = 'lms/communication/create_topic.html'
    fields = ['title', 'content']

    def form_valid(self, form):
        forum = get_object_or_404(Forum, id=self.kwargs['forum_id'])
        form.instance.forum = forum
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Topic created successfully!')
        return super().form_valid(form)


class TopicDetailView(DetailView):
    """Topic detail with replies"""
    model = Topic
    template_name = 'lms/communication/topic_detail.html'
    context_object_name = 'topic'
    pk_url_kwarg = 'topic_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        topic = self.object

        # Get replies
        replies = Reply.objects.filter(
            topic=topic
        ).order_by('created_at')

        context['replies'] = replies
        return context


class ReplyTopicView(LoginRequiredMixin, CreateView):
    """Reply to forum topic"""
    model = Reply
    template_name = 'lms/communication/reply_topic.html'
    fields = ['content']

    def form_valid(self, form):
        topic = get_object_or_404(Topic, id=self.kwargs['topic_id'])
        form.instance.topic = topic
        form.instance.created_by = self.request.user

        # Update topic last activity
        topic.last_activity = timezone.now()
        topic.save()

        messages.success(self.request, 'Reply posted successfully!')
        return super().form_valid(form)


class NotificationListView(LoginRequiredMixin, ListView):
    """User notifications"""
    template_name = 'lms/communication/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class MarkNotificationReadView(LoginRequiredMixin, View):
    """Mark notification as read"""

    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=request.user
            )
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()

            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})


class MarkAllNotificationsReadView(LoginRequiredMixin, View):
    """Mark all notifications as read"""

    def post(self, request):
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )

        messages.success(request, 'All notifications marked as read.')
        return redirect('communication:notifications')


class AnnouncementListView(ListView):
    """List announcements"""
    model = Announcement
    template_name = 'lms/communication/announcements.html'
    context_object_name = 'announcements'
    paginate_by = 10

    def get_queryset(self):
        return Announcement.objects.filter(
            is_published=True
        ).order_by('-created_at')


class AnnouncementDetailView(DetailView):
    """Announcement detail"""
    model = Announcement
    template_name = 'lms/communication/announcement_detail.html'
    context_object_name = 'announcement'
    pk_url_kwarg = 'announcement_id'

    def get_queryset(self):
        return Announcement.objects.filter(is_published=True)


class SendMessageAPIView(LoginRequiredMixin, View):
    """API endpoint to send message"""

    def post(self, request):
        recipient_id = request.POST.get('recipient_id')
        subject = request.POST.get('subject')
        content = request.POST.get('content')

        try:
            recipient = User.objects.get(id=recipient_id)

            message = Message.objects.create(
                sender=request.user,
                recipient=recipient,
                subject=subject,
                content=content
            )

            return JsonResponse({
                'success': True,
                'message_id': message.id
            })

        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Recipient not found'
            })


class SendLessonMessageView(LoginRequiredMixin, View):
    """API endpoint to send lesson-specific messages"""

    def post(self, request):
        import json

        try:
            data = json.loads(request.body)
            lesson_id = data.get('lesson_id')
            message_content = data.get('message')
            context = data.get('context', 'lesson_help')

            # Validate lesson access
            from courses.models import Lesson
            from progress.models import Enrollment

            try:
                lesson = Lesson.objects.get(id=lesson_id, is_published=True)
                enrollment = Enrollment.objects.get(
                    student=request.user,
                    course=lesson.module.course,
                    status='active'
                )
            except (Lesson.DoesNotExist, Enrollment.DoesNotExist):
                return JsonResponse({
                    'success': False,
                    'error': 'Access denied or lesson not found'
                })

            # Create lesson-specific message
            # For now, we'll create a general message with lesson context
            # In a full implementation, this could create a specialized LessonMessage model

            # Find instructors for this course (users with staff status or specific role)
            from django.contrib.auth.models import User
            instructors = User.objects.filter(is_staff=True).first()

            if instructors:
                message = Message.objects.create(
                    sender=request.user,
                    recipient=instructors,
                    subject=f"Question about: {lesson.title}",
                    content=f"Lesson: {lesson.title}\nContext: {context}\n\nQuestion: {message_content}"
                )

                # Create notification for instructor
                Notification.objects.create(
                    user=instructors,
                    notification_type='message',
                    title=f"New lesson question from {request.user.get_full_name()}",
                    message=f"Question about lesson: {lesson.title}",
                    action_url=f"/lms/communication/messages/{message.id}/"
                )

            return JsonResponse({
                'success': True,
                'message_id': message.id if instructors else None,
                'message': 'Message sent successfully'
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while sending the message'
            })


class GetUnreadCountAPIView(LoginRequiredMixin, View):
    """API endpoint to get unread message count"""

    def get(self, request):
        unread_messages = Message.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        return JsonResponse({
            'unread_messages': unread_messages,
            'unread_notifications': unread_notifications,
            'total_unread': unread_messages + unread_notifications
        })
