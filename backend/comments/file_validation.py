"""
Проверка и обработка файлов, прикреплённых к комментарию.

- Картинки: JPG, GIF, PNG. Больше 320x240 — пропорционально уменьшить
- Текстовые файлы: TXT, не больше 100 КБ

Принцип: не доверяем расширению и Content-Type от клиента.
Тип определяем по реальному содержимому файла.
"""

import io
import os

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image, UnidentifiedImageError

# Максимальные размеры картинки
MAX_IMAGE_WIDTH = 320
MAX_IMAGE_HEIGHT = 240

# Форматы, которые Pillow должен распознать внутри файла
ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'GIF'}

# Лимит для текстового файла: 100 КБ
MAX_TEXT_FILE_SIZE = 100 * 1024

# Предохранитель для картинок: без него можно загрузить
# файл на 500 МБ и положить сервер при попытке его открыть
MAX_IMAGE_FILE_SIZE = 5 * 1024 * 1024

# Соответствие формата Pillow и расширения файла
FORMAT_TO_EXTENSION = {
    'JPEG': '.jpg',
    'PNG': '.png',
    'GIF': '.gif',
}


def _is_image(uploaded_file) -> bool:
    """
    Определяет, картинка ли это, по содержимому файла.

    Pillow читает заголовок (магические байты) — если файл
    переименовали из .exe в .jpg, verify() выбросит исключение.
    """
    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)
        image.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False
    finally:
        # Возвращаем указатель в начало: после verify() файл
        # нужно открывать заново, иначе дальнейшее чтение упадёт
        uploaded_file.seek(0)


def _process_image(uploaded_file) -> tuple[InMemoryUploadedFile, int, int]:
    """
    Проверяет формат картинки и уменьшает её, если нужно.

    Возвращает готовый файл и его итоговые размеры.
    """
    if uploaded_file.size > MAX_IMAGE_FILE_SIZE:
        raise ValidationError(
            f'Изображение слишком большое: максимум '
            f'{MAX_IMAGE_FILE_SIZE // (1024 * 1024)} МБ'
        )

    uploaded_file.seek(0)
    image = Image.open(uploaded_file)

    if image.format not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError(
            f'Недопустимый формат изображения. Разрешены: JPG, PNG, GIF'
        )

    image_format = image.format
    original_size = image.size

    # thumbnail уменьшает картинку, сохраняя пропорции,
    # и не трогает её, если она уже меньше заданных размеров.
    # LANCZOS — качественный алгоритм интерполяции.
    image.thumbnail((MAX_IMAGE_WIDTH, MAX_IMAGE_HEIGHT), Image.Resampling.LANCZOS)

    # Если размер не изменился, пересохранять файл незачем —
    # отдаём оригинал как есть
    if image.size == original_size:
        uploaded_file.seek(0)
        return uploaded_file, image.size[0], image.size[1]

    # Сохраняем уменьшенную версию в память
    buffer = io.BytesIO()

    save_kwargs = {}
    if image_format == 'JPEG':
        # JPEG с качеством 90 — незаметная глазу потеря, но файл меньше.
        # optimize дополнительно сжимает без потери качества
        save_kwargs = {'quality': 90, 'optimize': True}
    elif image_format == 'GIF':
        # save_all сохраняет все кадры анимации, а не только первый
        save_kwargs = {'save_all': True}

    image.save(buffer, format=image_format, **save_kwargs)
    buffer.seek(0)

    # Расширение приводим к реальному формату: если файл назывался
    # photo.png, но внутри JPEG — он станет photo.jpg
    base_name = os.path.splitext(uploaded_file.name)[0]
    new_name = base_name + FORMAT_TO_EXTENSION[image_format]

    processed = InMemoryUploadedFile(
        file=buffer,
        field_name=None,
        name=new_name,
        content_type=f'image/{image_format.lower()}',
        size=buffer.getbuffer().nbytes,
        charset=None,
    )

    return processed, image.size[0], image.size[1]


def _validate_text_file(uploaded_file) -> None:
    """
    Проверяет текстовый файл: размер и то, что это действительно текст.
    """
    if uploaded_file.size > MAX_TEXT_FILE_SIZE:
        raise ValidationError(
            f'Текстовый файл слишком большой: максимум '
            f'{MAX_TEXT_FILE_SIZE // 1024} КБ'
        )

    extension = os.path.splitext(uploaded_file.name)[1].lower()
    if extension != '.txt':
        raise ValidationError(
            'Недопустимый формат файла. '
            'Разрешены изображения (JPG, PNG, GIF) и текстовые файлы (TXT)'
        )

    # Проверяем содержимое: файл должен читаться как текст.
    # Так отсеивается переименованный в .txt бинарник.
    uploaded_file.seek(0)
    sample = uploaded_file.read(1024)
    uploaded_file.seek(0)

    try:
        sample.decode('utf-8')
    except UnicodeDecodeError:
        try:
            sample.decode('cp1251')
        except UnicodeDecodeError:
            raise ValidationError(
                'Файл не является текстовым или использует '
                'неподдерживаемую кодировку'
            )


def process_attachment(uploaded_file) -> dict:
    """
    Главная функция: определяет тип файла, проверяет и обрабатывает его.

    Возвращает словарь с готовым файлом и метаданными
    для создания объекта Attachment.
    """
    if uploaded_file is None:
        raise ValidationError('Файл не передан')

    original_name = uploaded_file.name

    # Сначала пробуем как картинку — это надёжнее,
    # чем смотреть на расширение
    if _is_image(uploaded_file):
        processed_file, width, height = _process_image(uploaded_file)
        return {
            'file': processed_file,
            'file_type': 'image',
            'original_name': original_name,
            'width': width,
            'height': height,
        }

    # Не картинка — проверяем как текстовый файл
    _validate_text_file(uploaded_file)
    return {
        'file': uploaded_file,
        'file_type': 'text',
        'original_name': original_name,
        'width': None,
        'height': None,
    }