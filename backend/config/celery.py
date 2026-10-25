"""
Настройка Celery для проекта.

Celery запускается отдельным процессом и не знает про Django,
поэтому здесь мы явно указываем ему, где лежат настройки.
"""

import os

from celery import Celery

# Сообщаем Celery, какой модуль настроек использовать
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Читаем настройки из settings.py, берём только переменные
# с префиксом CELERY_ — остальные Celery не касаются
app.config_from_object('django.conf:settings', namespace='CELERY')

# Ищем файлы tasks.py во всех установленных приложениях
# и регистрируем найденные задачи автоматически
app.autodiscover_tasks()