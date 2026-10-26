"""
Точка входа ASGI.

Здесь HTTP и WebSocket разводятся по разным обработчикам:
обычные запросы идут в Django как раньше,
WebSocket — в Channels.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django инициализируется до импорта routing:
# иначе при загрузке consumers.py модели ещё не готовы
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from comments.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    # Обычные HTTP-запросы обрабатывает стандартное Django-приложение
    'http': django_asgi_app,

    # WebSocket: AllowedHostsOriginValidator пропускает соединения
    # только с доменов из ALLOWED_HOSTS — защита от подключения
    # с чужого сайта
    'websocket': AllowedHostsOriginValidator(
        URLRouter(websocket_urlpatterns)
    ),
})