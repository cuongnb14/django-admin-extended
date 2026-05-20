from django.apps import AppConfig


class SampleAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "admin_extended.tests.example_project.sample_app"
    label = "sample_app"
