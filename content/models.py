from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from courses.models import Lesson

User = get_user_model()


class ContentItem(models.Model):
    """
    Reusable content items that can be attached to lessons
    """
    CONTENT_TYPES = [
        ('text', 'Text Content'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('presentation', 'Presentation'),
        ('document', 'Document'),
        ('interactive', 'Interactive Content'),
        ('image', 'Image'),
        ('infographic', 'Infographic'),
    ]
    
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=30, choices=CONTENT_TYPES)
    content = models.TextField(blank=True, help_text="Text content or description")
    file_path = models.FileField(upload_to='content/', blank=True, null=True)
    external_url = models.URLField(blank=True, help_text="External resource URL")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional content metadata")
    tags = models.JSONField(default=list, blank=True, help_text="Content tags for search")
    is_public = models.BooleanField(default=False, help_text="Available to all users")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_content')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"
    
    class Meta:
        verbose_name = "Content Item"
        verbose_name_plural = "Content Items"
        ordering = ['-created_at']


class InteractiveExercise(models.Model):
    """
    Interactive exercises and activities
    """
    EXERCISE_TYPES = [
        ('case_study', 'Case Study Analysis'),
        ('group_work', 'Group Work'),
        ('individual_reflection', 'Individual Reflection'),
        ('scamper', 'SCAMPER Technique'),
        ('swot_analysis', 'SWOT Analysis'),
        ('business_plan', 'Business Plan Development'),
        ('brainstorming', 'Brainstorming Session'),
        ('role_play', 'Role Playing'),
        ('simulation', 'Business Simulation'),
    ]
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='interactive_exercises')
    title = models.CharField(max_length=200)
    instructions = models.TextField(help_text="Detailed instructions for the exercise")
    exercise_type = models.CharField(max_length=30, choices=EXERCISE_TYPES)
    exercise_data = models.JSONField(help_text="Exercise-specific data structure")
    time_limit = models.IntegerField(null=True, blank=True, help_text="Time limit in minutes")
    is_graded = models.BooleanField(default=False)
    max_score = models.IntegerField(default=100)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.lesson.title} - {self.title}"
    
    class Meta:
        verbose_name = "Interactive Exercise"
        verbose_name_plural = "Interactive Exercises"


class Resource(models.Model):
    """
    Downloadable resources and reference materials
    """
    RESOURCE_TYPES = [
        ('document', 'Document'),
        ('template', 'Template'),
        ('tool', 'Business Tool'),
        ('external_link', 'External Link'),
        ('video', 'Video Resource'),
        ('audio', 'Audio Resource'),
        ('infographic', 'Infographic'),
        ('checklist', 'Checklist'),
    ]
    
    ACCESS_LEVELS = [
        ('public', 'Public'),
        ('enrolled', 'Enrolled Students Only'),
        ('premium', 'Premium Members Only'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    resource_type = models.CharField(max_length=30, choices=RESOURCE_TYPES)
    file_path = models.FileField(upload_to='resources/', blank=True, null=True)
    external_url = models.URLField(blank=True)
    category = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=list, blank=True)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVELS, default='public')
    download_count = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_resources')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title
    
    def increment_download_count(self):
        self.download_count += 1
        self.save(update_fields=['download_count'])
    
    class Meta:
        verbose_name = "Resource"
        verbose_name_plural = "Resources"
        ordering = ['-created_at']


class LessonContent(models.Model):
    """
    Link lessons to content items
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='content_items')
    content_item = models.ForeignKey(ContentItem, on_delete=models.CASCADE, related_name='lesson_links')
    sort_order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['lesson', 'content_item']
        ordering = ['lesson', 'sort_order']
        verbose_name = "Lesson Content"
        verbose_name_plural = "Lesson Contents"


class LessonResource(models.Model):
    """
    Link lessons to resources
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='lesson_resources')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='lesson_links')
    sort_order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['lesson', 'resource']
        ordering = ['lesson', 'sort_order']
        verbose_name = "Lesson Resource"
        verbose_name_plural = "Lesson Resources"


class ContentLibrary(models.Model):
    """
    Organized content library for easy content management
    """
    LIBRARY_TYPES = [
        ('templates', 'Business Templates'),
        ('case_studies', 'Case Studies'),
        ('tools', 'Business Tools'),
        ('presentations', 'Presentations'),
        ('videos', 'Video Library'),
        ('documents', 'Documents'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    library_type = models.CharField(max_length=30, choices=LIBRARY_TYPES)
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_libraries')
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Content Library"
        verbose_name_plural = "Content Libraries"
        ordering = ['name']


class LibraryItem(models.Model):
    """
    Items within content libraries
    """
    library = models.ForeignKey(ContentLibrary, on_delete=models.CASCADE, related_name='items')
    content_item = models.ForeignKey(ContentItem, on_delete=models.CASCADE, related_name='library_items')
    sort_order = models.IntegerField(default=0)
    featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['library', 'content_item']
        ordering = ['library', 'sort_order']
        verbose_name = "Library Item"
        verbose_name_plural = "Library Items"

