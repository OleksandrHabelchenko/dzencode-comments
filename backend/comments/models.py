import os
from django.db import models
from django.core.validators import RegexValidator


class Comment(models.Model):
    """
    Комментарий пользователя.

    Поддерживает бесконечную вложенность через self-FK:
    parent = None  -> заглавный комментарий (отображается в таблице)
    parent = Comment -> ответ на другой комментарий (каскадное дерево)
    """

    # --- Связь родитель-потомок ---
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,     # удалили родителя -> удалились все ответы
        null=True,
        blank=True,
        related_name='replies',       # доступ к ответам: comment.replies.all()
        verbose_name='Родительский комментарий',
    )

    # --- Данные пользователя (требования ТЗ) ---
    user_name = models.CharField(
        max_length=50,
        validators=[
            # Только латиница и цифры — требование ТЗ.
            # Валидация и здесь, и на уровне сериализатора, и на фронте.
            # Латинские буквы, цифры и пробелы между ними
            RegexValidator(
                regex=r'^[a-zA-Z0-9]+( [a-zA-Z0-9]+)*$',
                message='User Name может содержать только латинские буквы, цифры и пробелы',
            )
        ],
        verbose_name='Имя пользователя',
    )

    email = models.EmailField(
        verbose_name='E-mail',
    )

    home_page = models.URLField(
        blank=True,                   # единственное необязательное поле по ТЗ
        default='',
        verbose_name='Домашняя страница',
    )

    # --- Текст сообщения ---
    text = models.TextField(
        verbose_name='Текст сообщения',
    )

    # --- Служебные поля ---
    created_at = models.DateTimeField(
        auto_now_add=True,            # проставляется автоматически при создании
        db_index=True,                # индекс: по этому полю идёт сортировка по умолчанию
        verbose_name='Дата добавления',
    )

    # Данные, помогающие идентифицировать клиента (требование ТЗ).
    # Заполняются на сервере из запроса, пользователь их не вводит.
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP-адрес',
    )

    user_agent = models.TextField(
        blank=True,
        default='',
        verbose_name='User-Agent браузера',
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        # Сортировка по умолчанию — LIFO: новые сверху.
        ordering = ['-created_at']
        indexes = [
            # Составной индекс ускоряет главный запрос:
            # "взять заглавные комментарии, отсортировать по дате"
            models.Index(fields=['parent', '-created_at']),
        ]

    def __str__(self):
        return f'{self.user_name}: {self.text[:50]}'

    @property
    def is_root(self) -> bool:
        """Заглавный комментарий (не ответ) — такие выводятся в таблице."""
        return self.parent_id is None


def attachment_upload_path(instance, filename: str) -> str:
    """
    Путь для загруженного файла: media/attachments/2026/10/24/имя_файла.
    Разбивка по датам не даёт тысячам файлов скопиться в одной папке.
    """
    from django.utils import timezone
    today = timezone.now()
    return os.path.join('attachments', today.strftime('%Y/%m/%d'), filename)


class Attachment(models.Model):
    """
    Файл, прикреплённый к комментарию: картинка или текстовый файл.

    Вынесен в отдельную модель, а не в поле Comment:
    так проще расширять (несколько файлов к одному комментарию)
    и хранить метаданные каждого файла.
    """

    class FileType(models.TextChoices):
        """Тип вложения. TextChoices — читаемые значения в БД вместо цифр."""
        IMAGE = 'image', 'Изображение'
        TEXT = 'text', 'Текстовый файл'

    comment = models.OneToOneField(
        Comment,
        on_delete=models.CASCADE,     # удалили комментарий -> удалилось вложение
        related_name='attachment',
        verbose_name='Комментарий',
    )

    file = models.FileField(
        upload_to=attachment_upload_path,
        verbose_name='Файл',
    )

    file_type = models.CharField(
        max_length=10,
        choices=FileType.choices,
        verbose_name='Тип файла',
    )

    original_name = models.CharField(
        max_length=255,
        verbose_name='Исходное имя файла',
    )

    # Размеры нужны фронтенду, чтобы зарезервировать место под картинку
    # до её загрузки — иначе страница будет "прыгать".
    width = models.PositiveIntegerField(null=True, blank=True, verbose_name='Ширина')
    height = models.PositiveIntegerField(null=True, blank=True, verbose_name='Высота')

    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'

    def __str__(self):
        return f'{self.get_file_type_display()}: {self.original_name}'