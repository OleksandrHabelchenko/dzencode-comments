"""
Команда для наполнения базы тестовыми данными.

Запуск:
    python manage.py seed_comments --count 60

Нужна для проверки пагинации и сортировки на реальном объёме.
В продакшене не используется.
"""

import random

from django.core.management.base import BaseCommand

from comments.models import Comment

NAMES = [
    'AlexSmith', 'MariaK', 'JohnDoe', 'Zebra99', 'anna2024',
    'BobMartin', 'CarlaRuiz', 'DmitryP', 'EvaGreen', 'FrankM',
    'GinaLee', 'HansWeber', 'IvanD', 'JuliaR', 'KevinO',
]

TEXTS = [
    'Отличная статья, спасибо!',
    'Не согласен с выводами, но написано интересно.',
    'А можно подробнее про <strong>второй пункт</strong>?',
    'Попробовал <code>docker compose up</code> — всё заработало.',
    'Хороший разбор, добавил в закладки.',
    'Было бы здорово увидеть продолжение.',
    'Спасибо, помогло решить мою задачу.',
]


class Command(BaseCommand):
    help = 'Создаёт тестовые комментарии для проверки пагинации'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=60,
            help='Сколько заглавных комментариев создать',
        )
        parser.add_argument(
            '--replies',
            type=int,
            default=2,
            help='Максимум ответов на каждый комментарий',
        )

    def handle(self, *args, **options):
        count = options['count']
        max_replies = options['replies']

        created_roots = 0
        created_replies = 0

        for index in range(count):
            name = random.choice(NAMES)
            root = Comment.objects.create(
                user_name=f'{name}{index}',
                email=f'{name.lower()}{index}@example.com',
                text=random.choice(TEXTS),
                home_page='https://example.com' if index % 3 == 0 else '',
            )
            created_roots += 1

            # Случайное количество ответов, чтобы дерево
            # выглядело правдоподобно, а не одинаково
            for reply_index in range(random.randint(0, max_replies)):
                Comment.objects.create(
                    parent=root,
                    user_name=f'Reply{index}x{reply_index}',
                    email=f'reply{index}x{reply_index}@example.com',
                    text=random.choice(TEXTS),
                )
                created_replies += 1

        self.stdout.write(self.style.SUCCESS(
            f'Создано: {created_roots} заглавных, {created_replies} ответов'
        ))
