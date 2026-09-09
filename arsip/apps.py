from django.apps import AppConfig


class ArsipConfig(AppConfig):
    name = 'arsip'

    def ready(self):
        import arsip.signals  # noqa

