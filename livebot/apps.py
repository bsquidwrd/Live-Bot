from django.apps import AppConfig


class LivebotConfig(AppConfig):
    name = 'livebot'

    def ready(self):
        import livebot.signals
