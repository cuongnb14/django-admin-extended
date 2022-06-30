from django.apps import AppConfig


class AdminExtendedConfig(AppConfig):
    name = 'admin_extended'
    verbose_name = 'Admin Extended'

    def ready(self):
        pass
