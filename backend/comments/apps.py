from django.apps import AppConfig


class CommentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comments'
    verbose_name = 'Комментарии'

    def ready(self):
        """
        Вызывается один раз при старте приложения.
        Импорт регистрирует обработчики сигналов —
        без него декораторы @receiver не сработают.
        """
        from . import signals  # noqa: F401