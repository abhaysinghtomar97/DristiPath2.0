from django.apps import AppConfig

class TrackingAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracking_app'

    def ready(self):
        # import signals to attach post_save handlers
        try:
            import tracking_app.signals  # noqa
        except Exception:
            # avoid raising during migrations if module import fails temporarily
            pass
