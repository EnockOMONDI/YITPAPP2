from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from courses.models import Course, Module, Lesson, Category
from assessments.models import Quiz, Question


class CourseTemplate(models.Model):
    """
    Pre-built course templates for quick course creation
    """
    TEMPLATE_TYPES = [
        ('basic', 'Basic Course'),
        ('video_series', 'Video Series'),
        ('workshop', 'Workshop'),
        ('certification', 'Certification Program'),
        ('mini_course', 'Mini Course'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='basic')
    structure = models.JSONField(help_text="Course outline template with modules and lessons")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    estimated_duration = models.IntegerField(help_text="Estimated duration in hours", default=10)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_course_templates')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Course Template"
        verbose_name_plural = "Course Templates"
        ordering = ['name']


class ContentBlock(models.Model):
    """
    Reusable content blocks for lessons
    """
    CONTENT_TYPES = [
        ('text', 'Text Content'),
        ('video', 'Video'),
        ('image', 'Image'),
        ('document', 'Document'),
        ('quiz', 'Quiz'),
        ('exercise', 'Interactive Exercise'),
        ('code', 'Code Block'),
        ('callout', 'Callout/Note'),
    ]

    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content = models.JSONField(help_text="Content data structure")
    description = models.TextField(blank=True)
    is_template = models.BooleanField(default=False, help_text="Available as template for other instructors")
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_content_blocks')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"

    class Meta:
        verbose_name = "Content Block"
        verbose_name_plural = "Content Blocks"
        ordering = ['-created_at']


class QuestionBank(models.Model):
    """
    Reusable question repository for assessments
    """
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
        ('matching', 'Matching'),
        ('fill_blank', 'Fill in the Blank'),
    ]

    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    options = models.JSONField(default=list, blank=True, help_text="Options for multiple choice questions")
    correct_answer = models.TextField(help_text="Correct answer or answer key")
    explanation = models.TextField(blank=True, help_text="Explanation for the correct answer")
    points = models.IntegerField(default=1)
    difficulty_level = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ], default='medium')
    subject_area = models.CharField(max_length=100, blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    is_public = models.BooleanField(default=False, help_text="Available to all instructors")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_questions')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.question_text[:50]}... ({self.get_question_type_display()})"

    class Meta:
        verbose_name = "Question Bank Item"
        verbose_name_plural = "Question Bank"
        ordering = ['-created_at']


class CourseBuilderSession(models.Model):
    """
    Track course building sessions for auto-save functionality
    """
    SESSION_STATUS = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_sessions')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    session_data = models.JSONField(default=dict, help_text="Auto-saved course data")
    current_step = models.IntegerField(default=1, help_text="Current wizard step (1-5)")
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='active')
    last_saved = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        course_title = self.course.title if self.course else "New Course"
        return f"{self.instructor.get_full_name()} - {course_title}"

    class Meta:
        verbose_name = "Course Builder Session"
        verbose_name_plural = "Course Builder Sessions"
        ordering = ['-last_saved']
