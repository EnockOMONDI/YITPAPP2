from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
from taggit.managers import TaggableManager
from html import unescape
from django.utils.html import strip_tags
from shortuuid.django_fields import ShortUUIDField
from pyuploadcare.dj.models import ImageField
from ckeditor.fields import RichTextField
from django.core.validators import URLValidator

class Event(models.Model):
    EVENT_TYPES = (
        ('PHYSICAL', 'Physical Event'),
        ('ONLINE', 'Online Event'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=200)
    date = models.DateTimeField()
    event_type = models.CharField(max_length=10, choices=EVENT_TYPES, default='PHYSICAL')
    location = models.CharField(max_length=200, blank=True, null=True)  # For physical events
    online_url = models.URLField(max_length=500, blank=True, null=True, validators=[URLValidator()])  # For online events
    image = ImageField(blank=True, null=True, manual_crop="4:4",)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = TaggableManager()
    featured = models.BooleanField(default=False)
    content = RichTextField()
    views = models.PositiveIntegerField(default=0)
    category = models.ForeignKey('EventCategory', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Events"
        verbose_name_plural = "Events "
    
    def __str__(self):
        return self.title[0:10]

    class Meta:
        ordering = ['-date']

        
    def clean(self):
        super().clean()
        if self.event_type == 'PHYSICAL' and not self.location:
            raise ValidationError('Location is required for physical events')
        if self.event_type == 'ONLINE' and not self.online_url:
            raise ValidationError('Online URL is required for virtual events')

    def get_location_display(self):
        if self.event_type == 'ONLINE':
            return "Online Event"
        return self.location
    

class EventCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class EventComment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='eventcomments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.comment[0:20]

