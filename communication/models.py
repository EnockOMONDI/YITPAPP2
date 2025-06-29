from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from courses.models import Course

User = get_user_model()


class Forum(models.Model):
    """
    Discussion forums for courses
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='forums')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_moderated = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_forums')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def total_topics(self):
        return self.topics.count()
    
    @property
    def total_posts(self):
        return sum(topic.replies.count() + 1 for topic in self.topics.all())
    
    class Meta:
        verbose_name = "Forum"
        verbose_name_plural = "Forums"
        ordering = ['course', 'title']


class Topic(models.Model):
    """
    Discussion topics within forums
    """
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    view_count = models.IntegerField(default=0)
    reply_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_topics')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def update_reply_count(self):
        """Update reply count"""
        self.reply_count = self.replies.count()
        self.save(update_fields=['reply_count'])
    
    @property
    def last_reply(self):
        """Get the last reply"""
        return self.replies.order_by('-created_at').first()
    
    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topics"
        ordering = ['-is_pinned', '-updated_at']


class Reply(models.Model):
    """
    Replies to forum topics
    """
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='replies')
    content = models.TextField()
    parent_reply = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_replies')
    is_solution = models.BooleanField(default=False, help_text="Mark as solution to the topic")
    like_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_replies')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Reply to {self.topic.title} by {self.created_by.get_full_name()}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update topic reply count
        self.topic.update_reply_count()
    
    class Meta:
        verbose_name = "Reply"
        verbose_name_plural = "Replies"
        ordering = ['created_at']


class Message(models.Model):
    """
    Private messages between users
    """
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    sent_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"From {self.sender.get_full_name()} to {self.recipient.get_full_name()}: {self.subject}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    class Meta:
        verbose_name = "Message"
        verbose_name_plural = "Messages"
        ordering = ['-sent_at']


class Feedback(models.Model):
    """
    Feedback system for various content types
    """
    CONTENT_TYPES = [
        ('lesson', 'Lesson'),
        ('assignment', 'Assignment'),
        ('quiz', 'Quiz'),
        ('course', 'Course'),
        ('instructor', 'Instructor'),
    ]
    
    FEEDBACK_TYPES = [
        ('instructor', 'Instructor Feedback'),
        ('peer', 'Peer Feedback'),
        ('self_assessment', 'Self Assessment'),
        ('system', 'System Generated'),
    ]
    
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPES)
    object_id = models.IntegerField()
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    rating = models.IntegerField(null=True, blank=True, help_text="1-5 star rating")
    comment = models.TextField(blank=True)
    is_anonymous = models.BooleanField(default=False)
    given_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedback')
    received_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='received_feedback')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Feedback on {self.content_type} by {self.given_by.get_full_name()}"
    
    class Meta:
        verbose_name = "Feedback"
        verbose_name_plural = "Feedback"
        ordering = ['-created_at']


class Announcement(models.Model):
    """
    Course announcements and notifications
    """
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='normal')
    is_published = models.BooleanField(default=False)
    publish_date = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_announcements')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def is_active(self):
        """Check if announcement is currently active"""
        now = timezone.now()
        if not self.is_published or now < self.publish_date:
            return False
        if self.expire_date and now > self.expire_date:
            return False
        return True
    
    class Meta:
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"
        ordering = ['-priority', '-publish_date']


class Notification(models.Model):
    """
    User notifications system
    """
    NOTIFICATION_TYPES = [
        ('course_enrollment', 'Course Enrollment'),
        ('assignment_due', 'Assignment Due'),
        ('quiz_available', 'Quiz Available'),
        ('grade_posted', 'Grade Posted'),
        ('forum_reply', 'Forum Reply'),
        ('message_received', 'Message Received'),
        ('achievement_earned', 'Achievement Earned'),
        ('announcement', 'Announcement'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    action_url = models.URLField(blank=True, help_text="URL to navigate when notification is clicked")
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Notification for {self.user.get_full_name()}: {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']


class StudyGroup(models.Model):
    """
    Student study groups for collaborative learning
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='study_groups')
    members = models.ManyToManyField(User, through='StudyGroupMembership', related_name='study_groups')
    is_public = models.BooleanField(default=True, help_text="Allow anyone to join")
    max_members = models.IntegerField(default=10)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_study_groups')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.course.title} - {self.name}"
    
    @property
    def member_count(self):
        return self.members.count()
    
    @property
    def is_full(self):
        return self.member_count >= self.max_members
    
    class Meta:
        verbose_name = "Study Group"
        verbose_name_plural = "Study Groups"
        ordering = ['course', 'name']


class StudyGroupMembership(models.Model):
    """
    Study group membership with roles
    """
    ROLE_CHOICES = [
        ('member', 'Member'),
        ('moderator', 'Moderator'),
        ('leader', 'Leader'),
    ]
    
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.study_group.name} ({self.role})"
    
    class Meta:
        unique_together = ['study_group', 'user']
        verbose_name = "Study Group Membership"
        verbose_name_plural = "Study Group Memberships"

