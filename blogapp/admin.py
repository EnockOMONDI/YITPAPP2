from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from blogapp.models import Post, Comment, Category, StaticContent
from import_export.admin import ImportExportModelAdmin, ImportExportActionModelAdmin
from import_export import resources
from import_export.formats.base_formats import XLSX
from .resources import PostResource, CategoryResource, CommentResource
from .utils import create_blog_import_template, validate_import_file
import logging

logger = logging.getLogger(__name__)

class StaticContentAdmin(admin.ModelAdmin):
    list_display = ('section_name', 'content')
    search_fields = ['section_name']

class ArticleAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    """
    Enhanced Blog Post Admin with comprehensive Excel import/export functionality
    """
    resource_class = PostResource
    formats = [XLSX]  # Only allow Excel format for consistency

    # Display and filtering
    search_fields = ['title', 'Author', 'content']
    list_display = ('title', 'status', 'category', 'user', 'featured', 'trending', 'date', 'views')
    list_editable = ['status', 'category', 'featured', 'trending']
    list_filter = ('category', 'status', 'featured', 'trending', 'date')
    readonly_fields = ('views', 'date', 'pid')
    list_per_page = 25

    # Fieldsets for better organization
    fieldsets = (
        ('Content', {
            'fields': ('title', 'content', 'image'),
            'description': 'Main content and featured image for the blog post'
        }),
        ('Meta Information', {
            'fields': ('Author', 'category', 'tags'),
            'description': 'Author, categorization, and tagging information'
        }),
        ('Publishing Settings', {
            'fields': ('status', 'featured', 'trending'),
            'description': 'Publication status and promotional settings'
        }),
        ('Statistics & System', {
            'fields': ('views', 'date', 'pid'),
            'classes': ('collapse',),
            'description': 'System-generated statistics and identifiers'
        }),
    )

    # Import/Export settings
    import_template_name = 'admin/blogapp/post/import.html'
    export_template_name = 'admin/blogapp/post/export.html'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'user').prefetch_related('tags')

    def get_urls(self):
        """Add custom URLs for template download"""
        urls = super().get_urls()
        custom_urls = [
            path('download-template/', self.admin_site.admin_view(self.download_template), name='blogapp_post_download_template'),
        ]
        return custom_urls + urls

    def download_template(self, request):
        """Generate and download Excel import template"""
        try:
            response = create_blog_import_template()
            logger.info(f"Template downloaded by user: {request.user.username}")
            return response
        except Exception as e:
            logger.error(f"Error generating template: {str(e)}")
            messages.error(request, f"Error generating template: {str(e)}")
            return redirect('admin:blogapp_post_changelist')

    def changelist_view(self, request, extra_context=None):
        """Enhanced changelist view with import/export buttons"""
        extra_context = extra_context or {}
        extra_context.update({
            'has_import_permission': self.has_import_permission(request),
            'has_export_permission': self.has_export_permission(request),
            'download_template_url': reverse('admin:blogapp_post_download_template'),
        })
        return super().changelist_view(request, extra_context)

    def has_import_permission(self, request):
        """Check if user has permission to import"""
        return request.user.has_perm('blogapp.add_post') and request.user.has_perm('blogapp.change_post')

    def has_export_permission(self, request):
        """Check if user has permission to export"""
        return request.user.has_perm('blogapp.view_post')

    class Media:
        css = {
            'all': ('admin/css/yitp-blog-admin.css',)
        }
        js = ('admin/js/yitp-blog-admin.js',)

class CategoryAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    """Enhanced Category Admin with import/export functionality"""
    resource_class = CategoryResource
    formats = [XLSX]

    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'slug', 'active')
    list_editable = ('active',)
    search_fields = ['title', 'slug']
    list_filter = ('active',)


class CommentAdmin(ImportExportActionModelAdmin, ImportExportModelAdmin):
    """Enhanced Comment Admin with import/export functionality"""
    resource_class = CommentResource
    formats = [XLSX]

    list_display = ('post', 'full_name', 'email', 'active', 'date')
    list_editable = ('active',)
    list_filter = ('active', 'date', 'post__category')
    search_fields = ['comment', 'full_name', 'email', 'post__title']
    readonly_fields = ('date',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('post')

admin.site.register(Post, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(StaticContent, StaticContentAdmin)