from django.contrib import admin
from .models import (
    ContentItem, Resource, InteractiveExercise,
    ContentLibrary, LessonContent, LessonResource, LibraryItem
)

# Simple admin registrations for immediate functionality
admin.site.register(ContentItem)
admin.site.register(Resource)
admin.site.register(InteractiveExercise)
admin.site.register(ContentLibrary)
admin.site.register(LessonContent)
admin.site.register(LessonResource)
admin.site.register(LibraryItem)