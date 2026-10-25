from rest_framework import serializers

from .models import Comment, Attachment

from .captcha import validate_captcha

from django.core.exceptions import ValidationError as DjangoValidationError

from .text_validation import clean_comment_text

class AttachmentSerializer(serializers.ModelSerializer):
    """
    Вложение в формате JSON.
    file_url отдаёт полный адрес файла, чтобы фронтенду
    не пришлось самому склеивать путь.
    """

    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = ('id', 'file_url', 'file_type', 'original_name', 'width', 'height')

    def get_file_url(self, obj) -> str | None:
        """Абсолютный URL файла (http://host/media/...)."""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class CommentSerializer(serializers.ModelSerializer):
    """
    Комментарий вместе со всеми вложенными ответами.

    replies заполняется рекурсивно: каждый ответ сериализуется
    тем же классом, поэтому глубина дерева не ограничена.
    """
    
    attachment = AttachmentSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'parent',
            'user_name',
            'email',
            'home_page',
            'text',
            'created_at',
            'attachment',
            'replies',
        )
        read_only_fields = ('id', 'created_at')

    def get_replies(self, obj):
        """
        Ответы на этот комментарий.

        Используем obj.replies.all() без фильтров — тогда Django
        возьмёт данные из prefetch_related, который мы сделаем во вьюхе,
        и не пойдёт в базу за каждым уровнем отдельно.
        """
        replies = obj.replies.all()
        return CommentSerializer(replies, many=True, context=self.context).data


class CommentListSerializer(serializers.ModelSerializer):
    """
    Укороченный комментарий для таблицы заглавных комментариев.

    В таблице нужны только User Name, E-mail и дата — тянуть
    всё дерево ответов для каждой строки было бы расточительно.
    replies_count показывает, сколько ответов внутри.
    """

    replies_count = serializers.IntegerField(read_only=True)
    has_attachment = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'user_name',
            'email',
            'home_page',
            'text',
            'created_at',
            'replies_count',
            'has_attachment',
        )

    def get_has_attachment(self, obj) -> bool:
        """Есть ли прикреплённый файл — фронт покажет иконку скрепки."""
        return hasattr(obj, 'attachment')


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Приём нового комментария от пользователя.

    Отдельный класс от CommentSerializer, потому что
    на вход и на выход нужны разные наборы полей:
    клиент не присылает id, created_at, ip_address — их ставит сервер.
    """
    # Поля капчи приходят от клиента, но в модели их нет —
    # write_only означает "принять и проверить, в ответ не возвращать"
    captcha_key = serializers.CharField(write_only=True)
    captcha_value = serializers.CharField(write_only=True)

    class Meta:
        model = Comment
        fields = (
        'parent',
        'user_name',
        'email',
        'home_page',
        'text',
        'captcha_key',
        'captcha_value',
        )
        
    def validate(self, attrs):
        """
        Проверка капчи перед сохранением.

        Делаем это в validate(), а не в отдельном validate_captcha_value(),
        потому что нужны сразу два поля: ключ и введённое значение.
        """
        key = attrs.pop('captcha_key', None)
        value = attrs.pop('captcha_value', None)

        if not validate_captcha(key, value):
            raise serializers.ValidationError(
                {'captcha_value': 'Неверный код с картинки'}
            )

        return attrs

    def validate_parent(self, value):
        """
        Проверяем, что родительский комментарий существует.
        DRF проверит это и сам, но явная проверка даёт понятное сообщение.
        """
        if value is not None and not Comment.objects.filter(pk=value.pk).exists():
            raise serializers.ValidationError('Родительский комментарий не найден')
        return value

    def validate_text(self, value: str) -> str:
        """
        Проверяет и очищает текст сообщения.

        DRF ожидает свой тип исключения, поэтому ошибку Django
        переводим в serializers.ValidationError.
        """
        try:
            return clean_comment_text(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

    def create(self, validated_data):
        """
        Сохраняем комментарий, добавив данные клиента из запроса.
        Пользователь их не вводит — сервер берёт сам из HTTP-заголовков.
        """
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self._get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
        return super().create(validated_data)

    @staticmethod
    def _get_client_ip(request) -> str | None:
        """
        Реальный IP клиента.
        За nginx настоящий адрес лежит в X-Forwarded-For,
        REMOTE_ADDR в этом случае покажет IP самого прокси.
        """
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')