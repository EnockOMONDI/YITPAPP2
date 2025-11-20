from django.apps import AppConfig


class YitpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'yitp'

    def ready(self):
        # Import signal handlers
        import yitp.signals  # noqa: F401
