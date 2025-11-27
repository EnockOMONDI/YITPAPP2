from django.db import models
from django.apps import apps
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field

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

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = CKEditor5Field(
        'Description',
        config_name='course_content',
        blank=True,
        help_text="Rich text course description with formatting and media"
    )
    learning_objectives = CKEditor5Field(
        'Learning Objectives',
        config_name='course_content',
        blank=True,
        help_text="What students will learn - use rich text formatting"
    )
    prerequisites = models.TextField(blank=True, help_text="Required knowledge or skills")
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='beginner')
    estimated_duration = models.IntegerField(help_text="Estimated duration in hours")
    thumbnail_url = models.URLField(blank=True, help_text="Uploadcare CDN URL for the course image")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    enrollment_limit = models.IntegerField(null=True, blank=True, help_text="Maximum number of students")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')

    # Approval workflow fields
    submitted_for_review_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses_reviewed')
    review_notes = models.TextField(blank=True, help_text="Admin notes about the course review")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-submit for review when instructor creates course
        if not self.pk and self.status == 'draft':
            self.status = 'in_review'
            self.submitted_for_review_at = timezone.now()

        # Auto-publish when approved by admin
        if self.status == 'published' and not self.is_published:
            self.is_published = True
        elif self.status != 'published' and self.is_published:
            self.is_published = False

        super().save(*args, **kwargs)

        # Send email notification for course creation
        if not self.pk and self.status == 'in_review':
            self._send_course_creation_notification()

    def _send_course_creation_notification(self):
        """Send email notification to admin when course is created"""
        try:
            from users.email_utils import send_course_creation_notification
            send_course_creation_notification(self.instructor, self)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send course creation notification: {str(e)}")

    def submit_for_review(self, user=None):
        """Submit course for admin review"""
        if self.status == 'draft':
            self.status = 'in_review'
            self.submitted_for_review_at = timezone.now()
            self.save()
            self._send_course_creation_notification()
            return True
        return False

    def approve_course(self, admin_user, notes=""):
        """Approve course for publishing"""
        if self.status == 'in_review':
            self.status = 'approved'
            self.reviewed_at = timezone.now()
            self.reviewed_by = admin_user
            self.review_notes = notes
            self.save()
            return True
        return False

    def publish_course(self, admin_user, notes=""):
        """Publish approved course"""
        if self.status in ['approved', 'in_review']:
            self.status = 'published'
            self.is_published = True
            self.reviewed_at = timezone.now()
            self.reviewed_by = admin_user
            self.review_notes = notes
            self.save()
            return True
        return False

    def reject_course(self, admin_user, notes=""):
        """Reject course with feedback"""
        if self.status == 'in_review':
            self.status = 'rejected'
            self.reviewed_at = timezone.now()
            self.reviewed_by = admin_user
            self.review_notes = notes
            self.save()
            return True
        return False
    
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

    def _get_primary_instructor_name(self):
        """
        Resolve the instructor's display name, falling back to username
        when full name is unavailable.
        """
        if not self.instructor:
            return "Course Instructor"

        full_name = ""
        if hasattr(self.instructor, 'get_full_name'):
            full_name = (self.instructor.get_full_name() or '').strip()

        if full_name:
            return full_name

        return getattr(self.instructor, 'username', str(self.instructor))

    def _get_module_instructor_ids(self):
        """
        Helper to gather distinct instructor IDs assigned across this course's modules.
        """
        ids = self.modules.values_list('module_instructors__instructor_id', flat=True)
        return {pk for pk in ids if pk}
    def has_collaborators(self):
        """
        Determine if the course has additional active instructor assignments
        besides the primary instructor.
        """
        instructor_ids = self._get_module_instructor_ids()
        if not instructor_ids:
            return False
        if not self.instructor_id:
            return len(instructor_ids) > 1
        return any(pk != self.instructor_id for pk in instructor_ids)

    @property
    def instructor_display_name(self):
        """
        Display name for UI surfaces. Adds '(+ collaborators)' when there are
        additional instructors collaborating on the course.
        """
        name = self._get_primary_instructor_name()
        if self.has_collaborators:
            return f"{name} (+ collaborators)"
        return name

    def user_has_module_access(self, user):
        """
        Determine whether the given user can manage this course via module ownership.
        """
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        if self.instructor_id and user.id == self.instructor_id:
            return True
        return self.modules.filter(
            module_instructors__instructor=user,
            module_instructors__is_active=True
        ).exists()

    @property
    def quiz_set(self):
        """Get all quizzes for this course through its lessons"""
        try:
            from assessments.models import Quiz
            lesson_ids = self.modules.values_list('lessons__id', flat=True)
            return Quiz.objects.filter(lesson_id__in=lesson_ids)
        except ImportError:
            return Quiz.objects.none()

    @property
    def thumbnail_src(self):
        """Return Uploadcare thumbnail URL if provided"""
        return self.thumbnail_url or ''

    def get_ordered_lessons(self):
        """Get all lessons in the course ordered by module and lesson sort_order"""
        lessons = []
        for module in self.modules.filter(is_published=True).order_by('sort_order'):
            module_lessons = module.lessons.filter(is_published=True).order_by('sort_order')
            lessons.extend(module_lessons)
        return lessons

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
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.ensure_primary_instructor_assignment()

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    @property
    def total_lessons(self):
        return self.lessons.count()

    @property
    def active_instructors(self):
        """Return a queryset of instructors actively assigned to this module."""
        ModuleInstructor = apps.get_model('users', 'ModuleInstructor')
        active_assignments = ModuleInstructor.objects.filter(
            module=self,
            is_active=True
        ).values_list('instructor_id', flat=True)
        return User.objects.filter(id__in=active_assignments).distinct()

    def get_primary_instructor(self):
        """Return the primary instructor for this module, if set."""
        assignment = self.module_instructors.filter(
            assignment_role='primary_instructor',
            is_active=True
        ).select_related('instructor').first()
        if assignment:
            return assignment.instructor
        return self.course.instructor

    def ensure_primary_instructor_assignment(self):
        """Ensure the course's designated instructor owns this module."""
        if not self.course_id or not self.course.instructor_id:
            return
        ModuleInstructor = apps.get_model('users', 'ModuleInstructor')
        ModuleInstructor.objects.get_or_create(
            module=self,
            instructor=self.course.instructor,
            defaults={
                'assignment_role': 'primary_instructor',
                'assigned_by': self.course.instructor,
                'can_edit_content': True,
                'can_manage_enrollments': True,
                'can_grade_assessments': True,
                'can_view_analytics': True,
                'can_communicate_students': True,
                'can_publish_course': True,
                'is_active': True,
            }
        )
    
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
        ('document', 'Document (PDF)'),
        ('audio', 'Audio'),
        ('presentation', 'Presentation'),
        ('exercise', 'Interactive Exercise'),
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
    ]
    
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content = CKEditor5Field(
        'Content',
        config_name='lesson_content',
        blank=True,
        help_text="Rich text content with formatting, images, and interactive elements"
    )
    video_url = models.URLField(blank=True, help_text="YouTube, Vimeo, or other video URL")
    document_url = models.URLField(blank=True, help_text="Uploadcare URL for PDF documents")
    audio_url = models.URLField(blank=True, help_text="URL for audio content")
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
        Check if lesson is accessible for the given user based on prerequisites and trial boundaries
        """
        from progress.models import Enrollment, LessonProgress
        from .trial_service import TrialAccessService

        try:
            # Check if user is enrolled in the course (including trial enrollments)
            enrollment = Enrollment.objects.get(
                student=user,
                course=self.module.course,
                status__in=['active', 'completed']
            )
        except Enrollment.DoesNotExist:
            return False, "You must be enrolled in this course to access lessons."

        # Check trial access boundaries first
        trial_access = TrialAccessService.can_access_lesson(user, self)
        if trial_access['is_trial_user']:
            if not trial_access['can_access']:
                return False, trial_access['reason']
            # Trial user can access this lesson, continue with normal progression checks

        # First lesson in first module is always accessible (if within trial boundaries)
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

    @property
    def document_src(self):
        """Return stored URL for lesson documents"""
        if not self.document_url:
            return ''
        return self.document_url


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
