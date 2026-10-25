# Импортируем приложение Celery при запуске Django,
# чтобы декоратор @shared_task находил его автоматически
from .celery import app as celery_app

__all__ = ('celery_app',)