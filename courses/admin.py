from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib import messages
from django.db.models import Q
from .models import (
    Category, Course, Module, Lesson, CourseTag,
    CourseTagging, CourseReview
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Category admin interface
    """
    list_display = ('name', 'parent', 'sort_order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('sort_order', 'name')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """
    Enhanced course admin interface with role-based filtering
    """
    list_display = [
        'title_with_link', 'instructor_name', 'category', 'difficulty_level',
        'status_display', 'enrollment_count', 'is_published', 'is_featured', 'created_at'
    ]
    list_filter = [
        'status', 'difficulty_level', 'is_published', 'is_featured', 'category',
        'created_at', 'instructor', 'reviewed_by'
    ]
    search_fields = ['title', 'description', 'instructor__email', 'instructor__first_name', 'instructor__last_name']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'enrollment_count_display', 'submitted_for_review_at', 'reviewed_at']
    filter_horizontal = []

    fieldsets = (
        ('Course Information', {
            'fields': ('title', 'slug', 'description', 'learning_objectives')
        }),
        ('Course Details', {
            'fields': ('category', 'instructor', 'difficulty_level', 'estimated_duration')
        }),
        ('Pricing & Enrollment', {
            'fields': ('price', 'enrollment_limit', 'prerequisites')
        }),
        ('Status & Publishing', {
            'fields': ('status', 'is_published', 'is_featured')
        }),
        ('Review Information', {
            'fields': ('submitted_for_review_at', 'reviewed_at', 'reviewed_by', 'review_notes'),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': ('enrollment_count_display',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_courses', 'publish_courses', 'reject_courses', 'unpublish_courses', 'feature_courses', 'unfeature_courses']

    def get_queryset(self, request):
        """Filter courses based on instructor role"""
        qs = super().get_queryset(request)

        # System admins see all courses
        if request.user.is_superuser:
            return qs

        # Check if user has instructor profile
        try:
            instructor_profile = request.user.instructor_profile
            if instructor_profile.instructor_role == 'system_admin':
                return qs
            else:
                # Course instructors see only their courses
                return qs.filter(instructor=request.user)
        except:
            # Regular staff users see no courses
            return qs.none()

    def title_with_link(self, obj):
        """Display course title with link to course detail"""
        return format_html(
            '<a href="{}" style="color: #ff5d15; font-weight: bold; text-decoration: none;">{}</a>',
            reverse('admin:courses_course_change', args=[obj.pk]),
            obj.title
        )
    title_with_link.short_description = 'Course Title'
    title_with_link.admin_order_field = 'title'

    def instructor_name(self, obj):
        """Display instructor name with link to instructor profile"""
        if hasattr(obj.instructor, 'instructor_profile'):
            instructor_url = reverse('admin:users_instructorprofile_change',
                                   args=[obj.instructor.instructor_profile.pk])
            return format_html(
                '<a href="{}" style="color: #341C67; font-weight: bold;">{}</a>',
                instructor_url,
                obj.instructor.get_full_name() or obj.instructor.username
            )
        return obj.instructor.get_full_name() or obj.instructor.username
    instructor_name.short_description = 'Instructor'
    instructor_name.admin_order_field = 'instructor__first_name'

    def enrollment_count(self, obj):
        """Display enrollment count with styling"""
        count = obj.enrollments.filter(status='active').count()
        if count > 0:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: #6c757d; font-size: 11px;">0</span>'
        )
    enrollment_count.short_description = 'Enrollments'

    def enrollment_count_display(self, obj):
        """Display detailed enrollment statistics"""
        active_count = obj.enrollments.filter(status='active').count()
        total_count = obj.enrollments.count()
        return f"Active: {active_count} | Total: {total_count}"
    enrollment_count_display.short_description = 'Enrollment Statistics'

    def status_display(self, obj):
        """Display course status with color coding"""
        status_colors = {
            'draft': '#6c757d',
            'in_review': '#ffc107',
            'approved': '#28a745',
            'published': '#007bff',
            'rejected': '#dc3545',
            'archived': '#6c757d'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'

    def publish_courses(self, request, queryset):
        """Bulk action to publish courses"""
        updated = queryset.update(is_published=True)
        self.message_user(
            request,
            f'{updated} course(s) have been published.',
            messages.SUCCESS
        )
    publish_courses.short_description = "Publish selected courses"

    def unpublish_courses(self, request, queryset):
        """Bulk action to unpublish courses"""
        updated = queryset.update(is_published=False)
        self.message_user(
            request,
            f'{updated} course(s) have been unpublished.',
            messages.WARNING
        )
    unpublish_courses.short_description = "Unpublish selected courses"

    def feature_courses(self, request, queryset):
        """Bulk action to feature courses"""
        updated = queryset.update(is_featured=True)
        self.message_user(
            request,
            f'{updated} course(s) have been featured.',
            messages.SUCCESS
        )
    feature_courses.short_description = "Feature selected courses"

    def unfeature_courses(self, request, queryset):
        """Bulk action to unfeature courses"""
        updated = queryset.update(is_featured=False)
        self.message_user(
            request,
            f'{updated} course(s) have been unfeatured.',
            messages.INFO
        )
    unfeature_courses.short_description = "Unfeature selected courses"

    def approve_courses(self, request, queryset):
        """Bulk action to approve courses for publishing"""
        updated = 0
        for course in queryset.filter(status='in_review'):
            if course.approve_course(request.user, "Bulk approved by admin"):
                updated += 1
        self.message_user(
            request,
            f'{updated} course(s) have been approved.',
            messages.SUCCESS
        )
    approve_courses.short_description = "Approve selected courses"

    def reject_courses(self, request, queryset):
        """Bulk action to reject courses"""
        updated = 0
        for course in queryset.filter(status='in_review'):
            if course.reject_course(request.user, "Bulk rejected by admin"):
                updated += 1
        self.message_user(
            request,
            f'{updated} course(s) have been rejected.',
            messages.WARNING
        )
    reject_courses.short_description = "Reject selected courses"
    


class LessonInline(admin.TabularInline):
    """
    Inline admin for lessons within modules
    """
    model = Lesson
    extra = 0
    fields = ('title', 'content_type', 'sort_order', 'is_published', 'is_mandatory', 'estimated_duration')
    ordering = ('sort_order',)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """
    Enhanced module admin interface with role-based filtering
    """
    list_display = [
        'title_with_link', 'course_title', 'lesson_count',
        'sort_order', 'is_published', 'estimated_duration'
    ]
    list_filter = ['is_published', 'course', 'course__instructor', 'created_at']
    search_fields = ['title', 'description', 'course__title', 'course__instructor__first_name']
    readonly_fields = ['created_at', 'updated_at', 'lesson_count_display']
    inlines = [LessonInline]
    ordering = ['course', 'sort_order']

    fieldsets = (
        ('Module Information', {
            'fields': ('title', 'description', 'course')
        }),
        ('Settings', {
            'fields': ('sort_order', 'estimated_duration', 'is_published')
        }),
        ('Statistics', {
            'fields': ('lesson_count_display',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Filter modules based on instructor role"""
        qs = super().get_queryset(request)

        # System admins see all modules
        if request.user.is_superuser:
            return qs

        # Check if user has instructor profile
        try:
            instructor_profile = request.user.instructor_profile
            if instructor_profile.instructor_role == 'system_admin':
                return qs
            else:
                # Course instructors see only their course modules
                return qs.filter(course__instructor=request.user)
        except:
            # Regular staff users see no modules
            return qs.none()

    def title_with_link(self, obj):
        """Display module title with link"""
        return format_html(
            '<a href="{}" style="color: #ff5d15; font-weight: bold;">{}</a>',
            reverse('admin:courses_module_change', args=[obj.pk]),
            obj.title
        )
    title_with_link.short_description = 'Module Title'
    title_with_link.admin_order_field = 'title'

    def course_title(self, obj):
        """Display course title with link"""
        course_url = reverse('admin:courses_course_change', args=[obj.course.pk])
        return format_html(
            '<a href="{}" style="color: #341C67;">{}</a>',
            course_url,
            obj.course.title
        )
    course_title.short_description = 'Course'
    course_title.admin_order_field = 'course__title'

    def lesson_count(self, obj):
        """Display lesson count"""
        count = obj.lessons.count()
        published_count = obj.lessons.filter(is_published=True).count()
        return format_html(
            '<span style="color: #28a745;">{}</span> / <span style="color: #6c757d;">{}</span>',
            published_count, count
        )
    lesson_count.short_description = 'Lessons (Pub/Total)'

    def lesson_count_display(self, obj):
        """Display detailed lesson statistics"""
        total = obj.lessons.count()
        published = obj.lessons.filter(is_published=True).count()
        return f"Published: {published} | Total: {total}"
    lesson_count_display.short_description = 'Lesson Statistics'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """
    Lesson admin interface
    """
    list_display = ('title', 'module', 'content_type', 'sort_order', 'is_published', 'is_mandatory')
    list_filter = ('content_type', 'is_published', 'is_mandatory', 'module__course')
    search_fields = ('title', 'content', 'module__title')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('module', 'sort_order')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('module', 'title', 'content_type', 'sort_order')
        }),
        ('Content', {
            'fields': ('content', 'video_url', 'audio_url', 'presentation_file')
        }),
        ('Settings', {
            'fields': ('is_published', 'is_mandatory', 'estimated_duration')
        }),
        ('Learning Details', {
            'fields': ('learning_objectives', 'resources')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CourseTag)
class CourseTagAdmin(admin.ModelAdmin):
    """
    Course tag admin interface
    """
    list_display = ('name', 'slug', 'color')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CourseTagging)
class CourseTaggingAdmin(admin.ModelAdmin):
    """
    Course tagging admin interface
    """
    list_display = ('course', 'tag', 'created_at')
    list_filter = ('tag', 'created_at')
    search_fields = ('course__title', 'tag__name')


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    """
    Course review admin interface
    """
    list_display = ('course', 'student', 'rating', 'is_published', 'created_at')
    list_filter = ('rating', 'is_published', 'created_at')
    search_fields = ('course__title', 'student__email', 'review_text')
    readonly_fields = ('created_at', 'updated_at')
