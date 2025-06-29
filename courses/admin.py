from django.contrib import admin
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
    Course admin interface
    """
    list_display = ('title', 'instructor', 'category', 'difficulty_level', 'is_published', 'is_featured', 'created_at')
    list_filter = ('difficulty_level', 'is_published', 'is_featured', 'category', 'created_at')
    search_fields = ('title', 'description', 'instructor__email')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ()
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'description', 'instructor', 'category')
        }),
        ('Course Details', {
            'fields': ('learning_objectives', 'prerequisites', 'difficulty_level', 'estimated_duration')
        }),
        ('Media and Pricing', {
            'fields': ('thumbnail', 'price', 'enrollment_limit')
        }),
        ('Publication', {
            'fields': ('is_published', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


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
    Module admin interface
    """
    list_display = ('title', 'course', 'sort_order', 'is_published', 'estimated_duration')
    list_filter = ('is_published', 'course', 'created_at')
    search_fields = ('title', 'description', 'course__title')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [LessonInline]
    ordering = ('course', 'sort_order')


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
            'fields': ('content', 'video_url', 'presentation_file')
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

