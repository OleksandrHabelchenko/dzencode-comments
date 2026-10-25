from django.db.models import Count, Prefetch
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .captcha import create_captcha, validate_captcha

from .models import Comment
from .pagination import CommentPagination
from .serializers import (
    CommentSerializer,
    CommentListSerializer,
    CommentCreateSerializer,
)


class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/comments/  — таблица заглавных комментариев (25 на страницу)
    POST /api/comments/  — добавление нового комментария или ответа

    Поддерживает сортировку по User Name, E-mail и дате
    в обе стороны — требование ТЗ.
    """

    pagination_class = CommentPagination

    # Поля, по которым разрешена сортировка.
    # Белый список: клиент не может отсортировать по произвольному полю,
    # это защита от раскрытия структуры БД через параметры запроса.
    ALLOWED_ORDERING = {
        'user_name': 'user_name',
        'email': 'email',
        'created_at': 'created_at',
    }

    def get_serializer_class(self):
        """Для чтения — короткий сериализатор, для записи — свой."""
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentListSerializer

    def get_queryset(self):
        """
        Только заглавные комментарии (parent=None) — они идут в таблицу.
        Ответы на них подтягиваются отдельным запросом при раскрытии ветки.
        """
        queryset = Comment.objects.filter(parent__isnull=True)

        # annotate считает количество ответов одним SQL-запросом,
        # вместо отдельного запроса на каждую строку таблицы.
        queryset = queryset.annotate(replies_count=Count('descendants'))

        # select_related подтягивает вложение сразу,
        # чтобы не делать запрос на каждый комментарий (проблема N+1)
        queryset = queryset.select_related('attachment')

        return queryset.order_by(self._get_ordering())

    def _get_ordering(self) -> str:
        """
        Разбирает параметры ?ordering=user_name&direction=desc

        По умолчанию — LIFO (новые сверху), как требует ТЗ.
        """
        field = self.request.query_params.get('ordering', 'created_at')
        direction = self.request.query_params.get('direction', 'desc')

        # Неизвестное поле игнорируем и возвращаемся к сортировке по умолчанию
        db_field = self.ALLOWED_ORDERING.get(field, 'created_at')

        # Минус перед полем означает сортировку по убыванию
        return f'-{db_field}' if direction == 'desc' else db_field

    def create(self, request, *args, **kwargs):
        """
        Создание комментария.

        После сохранения отдаём объект полным сериализатором,
        чтобы фронт сразу получил созданную запись со всеми полями
        и мог вставить её в список без дополнительного запроса.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()

        output = CommentSerializer(comment, context={'request': request})
        return Response(output.data, status=status.HTTP_201_CREATED)


class CommentThreadView(generics.RetrieveAPIView):
    """
    GET /api/comments/<id>/  — один комментарий со всем деревом ответов.

    Вызывается, когда пользователь раскрывает ветку в таблице.
    """

    serializer_class = CommentSerializer

    def get_queryset(self):
        """
        Загружаем комментарий вместе с ответами.

        Prefetch с глубиной 3 уровня покрывает типичный случай.
        Если ветка глубже, Django догрузит остальное —
        но для большинства веток это один-два запроса вместо десятков.
        """
        replies_prefetch = Prefetch(
            'replies',
            queryset=Comment.objects.select_related('attachment').order_by('created_at'),
        )
        return Comment.objects.select_related('attachment').prefetch_related(
            replies_prefetch,
            'replies__replies',
            'replies__replies__replies',
        )

class CaptchaView(APIView):
    """
    GET /api/comments/captcha/ — новая капча.

    Фронтенд вызывает этот эндпоинт при открытии формы
    и при нажатии кнопки "обновить картинку".
    """

    def get(self, request):
        return Response(create_captcha())