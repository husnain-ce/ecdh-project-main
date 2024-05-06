from django.apps import AppConfig


class EhrappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ehrapp'

    def ready(self):
        import ehrapp.signal