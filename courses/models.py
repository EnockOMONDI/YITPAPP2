from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()


class Category(models.Model):
    """
    Course categories for organization
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    icon = models.CharField(max_length=50, blank=True, help_text="CSS icon class")
    color = models.CharField(max_length=7, default='#2563EB', help_text="Hex color code")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']


class Course(models.Model):
    """
    Main course model
    """
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    learning_objectives = models.TextField(help_text="What students will learn")
    prerequisites = models.TextField(blank=True, help_text="Required knowledge or skills")
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='beginner')
    estimated_duration = models.IntegerField(help_text="Estimated duration in hours")
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    enrollment_limit = models.IntegerField(null=True, blank=True, help_text="Maximum number of students")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def total_modules(self):
        return self.modules.count()
    
    @property
    def total_lessons(self):
        return sum(module.lessons.count() for module in self.modules.all())
    
    @property
    def enrolled_students_count(self):
        from progress.models import Enrollment
        return Enrollment.objects.filter(course=self, status='active').count()

    @property
    def quiz_set(self):
        """Get all quizzes for this course through its lessons"""
        try:
            from assessments.models import Quiz
            lesson_ids = self.modules.values_list('lessons__id', flat=True)
            return Quiz.objects.filter(lesson_id__in=lesson_ids)
        except ImportError:
            return Quiz.objects.none()
    
    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ['-created_at']


class Module(models.Model):
    """
    Course modules for organizing lessons
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    unlock_criteria = models.JSONField(default=dict, blank=True, help_text="Conditions for unlocking module")
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def total_lessons(self):
        return self.lessons.count()
    
    class Meta:
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ['course', 'sort_order']


class Lesson(models.Model):
    """
    Individual lessons within modules
    """
    CONTENT_TYPES = [
        ('text', 'Text Content'),
        ('video', 'Video'),
        ('presentation', 'Presentation'),
        ('exercise', 'Interactive Exercise'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content = models.TextField(blank=True, help_text="Text content or description")
    video_url = models.URLField(blank=True, help_text="YouTube, Vimeo, or other video URL")
    presentation_file = models.FileField(upload_to='presentations/', blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    is_published = models.BooleanField(default=False)
    is_mandatory = models.BooleanField(default=True)
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes")
    learning_objectives = models.TextField(blank=True)
    resources = models.JSONField(default=list, blank=True, help_text="Additional resources and links")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    def is_accessible_for_user(self, user):
        """
        Check if lesson is accessible for the given user based on prerequisites
        """
        from progress.models import Enrollment, LessonProgress

        try:
            # Check if user is enrolled in the course
            enrollment = Enrollment.objects.get(
                student=user,
                course=self.module.course,
                status='active'
            )
        except Enrollment.DoesNotExist:
            return False, "You must be enrolled in this course to access lessons."

        # First lesson in first module is always accessible
        if self.is_first_lesson_in_course():
            return True, "First lesson is always accessible."

        # Check if previous lesson is completed
        previous_lesson = self.get_previous_lesson()
        if previous_lesson:
            try:
                prev_progress = LessonProgress.objects.get(
                    enrollment=enrollment,
                    lesson=previous_lesson
                )
                if prev_progress.status != 'completed':
                    return False, f"You must complete '{previous_lesson.title}' before accessing this lesson."
            except LessonProgress.DoesNotExist:
                return False, f"You must complete '{previous_lesson.title}' before accessing this lesson."

        return True, "Lesson is accessible."

    def is_first_lesson_in_course(self):
        """Check if this is the first lesson in the entire course"""
        first_module = self.module.course.modules.filter(is_published=True).order_by('sort_order').first()
        if first_module and first_module == self.module:
            first_lesson = first_module.lessons.filter(is_published=True).order_by('sort_order').first()
            return first_lesson == self
        return False

    def get_previous_lesson(self):
        """Get the previous lesson in the course sequence"""
        # First, try to get previous lesson in same module
        prev_in_module = self.module.lessons.filter(
            sort_order__lt=self.sort_order,
            is_published=True
        ).order_by('-sort_order').first()

        if prev_in_module:
            return prev_in_module

        # If no previous lesson in current module, get last lesson from previous module
        prev_module = self.module.course.modules.filter(
            sort_order__lt=self.module.sort_order,
            is_published=True
        ).order_by('-sort_order').first()

        if prev_module:
            return prev_module.lessons.filter(is_published=True).order_by('-sort_order').first()

        return None

    def get_next_lesson(self):
        """Get the next lesson in the course sequence"""
        # First, try to get next lesson in same module
        next_in_module = self.module.lessons.filter(
            sort_order__gt=self.sort_order,
            is_published=True
        ).order_by('sort_order').first()

        if next_in_module:
            return next_in_module

        # If no next lesson in current module, get first lesson from next module
        next_module = self.module.course.modules.filter(
            sort_order__gt=self.module.sort_order,
            is_published=True
        ).order_by('sort_order').first()

        if next_module:
            return next_module.lessons.filter(is_published=True).order_by('sort_order').first()

        return None

    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
        ordering = ['module', 'sort_order']


class CourseTag(models.Model):
    """
    Tags for course categorization and search
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6B7280')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Course Tag"
        verbose_name_plural = "Course Tags"
        ordering = ['name']


class CourseTagging(models.Model):
    """
    Many-to-many relationship between courses and tags
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_tags')
    tag = models.ForeignKey(CourseTag, on_delete=models.CASCADE, related_name='tagged_courses')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['course', 'tag']
        verbose_name = "Course Tagging"
        verbose_name_plural = "Course Taggings"


class CourseReview(models.Model):
    """
    Student reviews and ratings for courses
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], help_text="1-5 star rating")
    review_text = models.TextField(blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.student.get_full_name()} ({self.rating} stars)"
    
    class Meta:
        unique_together = ['course', 'student']
        verbose_name = "Course Review"
        verbose_name_plural = "Course Reviews"
        ordering = ['-created_at']

