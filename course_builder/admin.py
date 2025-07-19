from django.contrib import admin
from .models import CourseTemplate, ContentBlock, QuestionBank, CourseBuilderSession


@admin.register(CourseTemplate)
class CourseTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'category', 'estimated_duration', 'is_active', 'created_by', 'created_at']
    list_filter = ['template_type', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'template_type', 'category')
        }),
        ('Template Configuration', {
            'fields': ('structure', 'estimated_duration', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContentBlock)
class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'is_template', 'created_by', 'created_at']
    list_filter = ['content_type', 'is_template', 'created_at']
    search_fields = ['title', 'description', 'tags']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content_type', 'description')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Settings', {
            'fields': ('is_template', 'tags')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(QuestionBank)
class QuestionBankAdmin(admin.ModelAdmin):
    list_display = ['question_text_short', 'question_type', 'difficulty_level', 'points', 'is_public', 'created_by', 'created_at']
    list_filter = ['question_type', 'difficulty_level', 'is_public', 'created_at']
    search_fields = ['question_text', 'subject_area', 'tags']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Question', {
            'fields': ('question_text', 'question_type', 'explanation')
        }),
        ('Answer Configuration', {
            'fields': ('options', 'correct_answer', 'points')
        }),
        ('Classification', {
            'fields': ('difficulty_level', 'subject_area', 'tags')
        }),
        ('Sharing', {
            'fields': ('is_public',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = "Question"

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CourseBuilderSession)
class CourseBuilderSessionAdmin(admin.ModelAdmin):
    list_display = ['instructor', 'course_title', 'current_step', 'status', 'last_saved']
    list_filter = ['status', 'current_step', 'last_saved', 'created_at']
    search_fields = ['instructor__username', 'instructor__first_name', 'instructor__last_name']
    readonly_fields = ['created_at', 'last_saved']

    fieldsets = (
        ('Session Information', {
            'fields': ('instructor', 'course', 'current_step', 'status')
        }),
        ('Session Data', {
            'fields': ('session_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_saved'),
            'classes': ('collapse',)
        }),
    )

    def course_title(self, obj):
        return obj.course.title if obj.course else "New Course"
    course_title.short_description = "Course"
