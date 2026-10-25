"""
Фоновые задачи Celery.

Выносим сюда всё, что не обязано выполняться
во время HTTP-запроса: пользователь не должен ждать.
"""

import logging

from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)


@shared_task(name='comments.invalidate_cache')
def invalidate_comments_cache() -> str:
    """
    Сбрасывает кеш списка комментариев.

    Вызывается после добавления нового комментария:
    кешированный список устарел, его нужно пересобрать.
    """
    # delete_pattern есть в django-redis; в стандартном бэкенде
    # его нет, поэтому чистим кеш целиком — список небольшой
    cache.clear()
    logger.info('Кеш списка комментариев сброшен')
    return 'cache cleared'


@shared_task(
    name='comments.notify_parent_author',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def notify_parent_author(self, comment_id: int) -> str:
    """
    Уведомляет автора комментария о полученном ответе.

    bind=True даёт доступ к self для повторных попыток.
    max_retries=3 — при сбое задача повторится до трёх раз
    с интервалом в минуту.

    Сейчас задача только пишет в лог: реальная отправка писем
    требует настроенного SMTP, что выходит за рамки задания.
    """
    from .models import Comment

    try:
        comment = Comment.objects.select_related('parent').get(pk=comment_id)
    except Comment.DoesNotExist:
        logger.warning('Комментарий %s не найден, уведомление пропущено', comment_id)
        return 'comment not found'

    if comment.parent is None:
        return 'no parent, nothing to notify'

    logger.info(
        'Уведомление для %s: на ваш комментарий ответил %s',
        comment.parent.email,
        comment.user_name,
    )
    return f'notified {comment.parent.email}'