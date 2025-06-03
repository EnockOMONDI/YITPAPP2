from django.apps import AppConfig


class BlogappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blogapp'  # Fixed to match actual directory name
    verbose_name = 'Blog Management'
