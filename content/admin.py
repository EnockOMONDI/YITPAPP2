from django.contrib import admin
from .models import (
    ContentItem, Resource, InteractiveExercise,
    ContentLibrary, LessonContent, LessonResource, LibraryItem
)

# Basic registers for models without heavy related lookups
admin.site.register(ContentItem)
admin.site.register(Resource)
admin.site.register(InteractiveExercise)


@admin.register(LessonContent)
class LessonContentAdmin(admin.ModelAdmin):
    """Optimized admin for LessonContent with query joining"""
    list_display = ['id', 'lesson_title', 'content_item_title', 'sort_order', 'is_required']
    list_filter = ['is_required', 'lesson__module__course']
    search_fields = ['lesson__title', 'content_item__title']
    list_select_related = ['lesson__module__course', 'content_item']
    list_per_page = 25
    ordering = ['lesson', 'sort_order']

    def lesson_title(self, obj):
        return obj.lesson.title
    lesson_title.short_description = 'Lesson'
    lesson_title.admin_order_field = 'lesson__title'

    def content_item_title(self, obj):
        return obj.content_item.title
    content_item_title.short_description = 'Content Item'
    content_item_title.admin_order_field = 'content_item__title'


@admin.register(LessonResource)
class LessonResourceAdmin(admin.ModelAdmin):
    """Optimized admin for LessonResource with query joining"""
    list_display = ['id', 'lesson_title', 'resource_title', 'sort_order', 'is_required']
    list_filter = ['is_required', 'lesson__module__course']
    search_fields = ['lesson__title', 'resource__title']
    list_select_related = ['lesson__module__course', 'resource']
    list_per_page = 25
    ordering = ['lesson', 'sort_order']

    def lesson_title(self, obj):
        return obj.lesson.title
    lesson_title.short_description = 'Lesson'
    lesson_title.admin_order_field = 'lesson__title'

    def resource_title(self, obj):
        return obj.resource.title
    resource_title.short_description = 'Resource'
    resource_title.admin_order_field = 'resource__title'


@admin.register(ContentLibrary)
class ContentLibraryAdmin(admin.ModelAdmin):
    """Optimized admin for ContentLibrary with query joining"""
    list_display = ['id', 'name', 'library_type', 'is_public', 'creator_name', 'created_at']
    list_filter = ['library_type', 'is_public']
    search_fields = ['name', 'description', 'created_by__username', 'created_by__email']
    list_select_related = ['created_by']
    list_per_page = 25
    ordering = ['name']

    def creator_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username
    creator_name.short_description = 'Created By'
    creator_name.admin_order_field = 'created_by__username'


@admin.register(LibraryItem)
class LibraryItemAdmin(admin.ModelAdmin):
    """Optimized admin for LibraryItem with query joining"""
    list_display = ['id', 'library_name', 'content_item_title', 'sort_order', 'featured']
    list_filter = ['featured', 'library']
    search_fields = ['library__name', 'content_item__title']
    list_select_related = ['library', 'content_item']
    list_per_page = 25
    ordering = ['library', 'sort_order']

    def library_name(self, obj):
        return obj.library.name
    library_name.short_description = 'Library'
    library_name.admin_order_field = 'library__name'

    def content_item_title(self, obj):
        return obj.content_item.title
    content_item_title.short_description = 'Content Item'
    content_item_title.admin_order_field = 'content_item__title'