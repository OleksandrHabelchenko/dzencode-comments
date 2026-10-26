"""
Сигналы Django — события внутри приложения.

Сигнал позволяет реагировать на сохранение модели,
не вписывая эту логику в сериализатор или вьюху:
код, который рассылает уведомления, отделён от кода,
который создаёт комментарии.
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .consumers import COMMENTS_GROUP
from .models import Comment

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Comment)
def broadcast_new_comment(sender, instance: Comment, created: bool, **kwargs):
    """
    Рассылает новый комментарий всем подключённым клиентам.

    created=True означает, что это новая запись, а не обновление
    существующей — рассылаем только новые.
    """
    if not created:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        logger.warning('Channel layer недоступен, рассылка пропущена')
        return

    # Сериализуем минимум данных: фронтенд догрузит остальное,
    # если понадобится. Чем меньше сообщение, тем быстрее доставка.
    payload = {
        'id': instance.id,
        'parent': instance.parent_id,
        'user_name': instance.user_name,
        'email': instance.email,
        'home_page': instance.home_page,
        'text': instance.text,
        'created_at': instance.created_at.isoformat(),
    }

    # Сигнал выполняется в синхронном коде, а channel_layer асинхронный —
    # async_to_sync перекидывает вызов между мирами
    async_to_sync(channel_layer.group_send)(
        COMMENTS_GROUP,
        {
            'type': 'comment.created',   # вызовет метод comment_created у consumer
            'comment': payload,
        },
    )

    logger.info('Комментарий %s разослан по WebSocket', instance.id)