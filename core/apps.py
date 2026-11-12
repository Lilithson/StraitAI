from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for project-wide, non-domain functionality."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
