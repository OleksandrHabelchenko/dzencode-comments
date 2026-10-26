"""
Маршруты WebSocket.

Отдельный файл от urls.py: HTTP и WebSocket — разные протоколы
со своими адресами, смешивать их в одном месте неудобно.
"""

from django.urls import path

from .consumers import CommentConsumer

websocket_urlpatterns = [
    path('ws/comments/', CommentConsumer.as_asgi()),
]