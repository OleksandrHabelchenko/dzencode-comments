"""
WebSocket-обработчик для комментариев.

Consumer — это аналог view, но для постоянного соединения:
view отвечает один раз и закрывается, consumer живёт,
пока открыта вкладка браузера.
"""

import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)

# Имя группы: все подключённые клиенты состоят в ней
# и получают одни и те же сообщения
COMMENTS_GROUP = 'comments'


class CommentConsumer(AsyncWebsocketConsumer):
    """
    Обрабатывает WebSocket-соединения на /ws/comments/.

    Клиент только слушает: отправка комментариев идёт
    обычным HTTP-запросом. Так проще — работают привычная
    валидация, капча и загрузка файлов.
    """

    async def connect(self):
        """
        Новое соединение: добавляем клиента в общую группу
        и подтверждаем подключение.
        """
        await self.channel_layer.group_add(COMMENTS_GROUP, self.channel_name)
        await self.accept()
        logger.info('WebSocket подключён: %s', self.channel_name)

    async def disconnect(self, close_code):
        """
        Соединение закрыто — убираем клиента из группы,
        чтобы сервер не пытался отправлять сообщения в никуда.
        """
        await self.channel_layer.group_discard(COMMENTS_GROUP, self.channel_name)
        logger.info('WebSocket отключён: %s', self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """
        Сообщения от клиента.

        Отвечаем только на ping — так фронтенд проверяет,
        что соединение живо, и не даёт прокси его разорвать.
        """
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def comment_created(self, event):
        """
        Обработчик события о новом комментарии.

        Имя метода соответствует типу сообщения comment.created:
        Channels заменяет точку на подчёркивание и вызывает этот метод
        у каждого клиента в группе.
        """
        await self.send(text_data=json.dumps({
            'type': 'comment.created',
            'comment': event['comment'],
        }))