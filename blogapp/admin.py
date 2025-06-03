from django.contrib import admin
from blogapp.models import Post, Comment, Category, StaticContent
from import_export.admin import ImportExportModelAdmin

class StaticContentAdmin(admin.ModelAdmin):
    list_display = ('section_name', 'content')
    search_fields = ['section_name']

class ArticleAdmin(ImportExportModelAdmin):
    search_fields = ['title']
    list_display = ('title', 'status', 'category', 'user', 'featured', 'trending')
    list_editable = ['status', 'category']
    list_filter = ('category', 'status')
    readonly_fields = ('views', 'date')
    fieldsets = (
        ('Content', {
            'fields': ('title', 'content', 'image')
        }),
        ('Meta', {
            'fields': ('Author', 'category', 'tags')
        }),
        ('Settings', {
            'fields': ('status', 'featured', 'trending')
        }),
        ('Statistics', {
            'fields': ('views', 'date'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'user')

class CategoryAdmin(ImportExportModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('title', 'active')

class CommentAdmin(ImportExportModelAdmin):
    list_display = ('post', 'full_name', 'email', 'active', 'date')
    list_editable = ('active',)
    list_filter = ('active', 'date')
    search_fields = ['comment', 'full_name', 'email']

admin.site.register(Post, ArticleAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(StaticContent, StaticContentAdmin)