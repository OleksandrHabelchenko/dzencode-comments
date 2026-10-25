"""
Генерация и проверка CAPTCHA.

Схема работы:
1. Клиент запрашивает капчу -> сервер создаёт код, рисует картинку,
   сохраняет код в кеше под случайным ключом
2. Клиенту уходит ключ (captcha_key) и картинка в base64
3. При отправке формы клиент присылает ключ и введённый текст
4. Сервер достаёт код из кеша по ключу и сравнивает

Правильный ответ клиенту не передаётся никогда.
"""

import base64
import io
import random
import string
import uuid

from django.core.cache import cache
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Длина кода на картинке
CAPTCHA_LENGTH = 5

# Сколько капча живёт в кеше (секунды).
# 10 минут: хватит заполнить форму, но украденный ключ быстро протухнет.
CAPTCHA_TTL = 600

# Размер изображения в пикселях
IMAGE_WIDTH = 160
IMAGE_HEIGHT = 60

# Префикс ключа в кеше, чтобы не пересекаться с другими данными
CACHE_PREFIX = 'captcha:'

# Символы для кода.
# Исключены похожие при чтении: 0/O, 1/I/l — иначе пользователь
# будет ошибаться не по своей вине.
ALPHABET = ''.join(
    c for c in string.ascii_uppercase + string.digits
    if c not in 'O0I1'
)


def _generate_code(length: int = CAPTCHA_LENGTH) -> str:
    """Случайный код из разрешённых символов."""
    return ''.join(random.choices(ALPHABET, k=length))


def _load_font(size: int = 32) -> ImageFont.FreeTypeFont:
    """
    Шрифт для текста на картинке.
    Пробуем системный DejaVu (есть в Debian-образе),
    если его нет — встроенный шрифт Pillow.
    """
    try:
        return ImageFont.truetype(
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size
        )
    except OSError:
        return ImageFont.load_default()


def _draw_image(code: str) -> bytes:
    """
    Рисует картинку с кодом и помехами.

    Помехи нужны, чтобы простой OCR не прочитал текст:
    случайный фон, линии поверх символов, точки, лёгкое размытие.
    """
    image = Image.new('RGB', (IMAGE_WIDTH, IMAGE_HEIGHT), color=(245, 245, 245))
    draw = ImageDraw.Draw(image)
    font = _load_font()

    # Символы рисуем по одному, со случайным смещением и цветом —
    # так сложнее разрезать картинку на одинаковые куски
    x = 12
    for char in code:
        y = random.randint(5, 18)
        color = (
            random.randint(0, 100),
            random.randint(0, 100),
            random.randint(0, 100),
        )
        draw.text((x, y), char, font=font, fill=color)
        x += random.randint(24, 30)

    # Линии-помехи поверх текста
    for _ in range(5):
        start = (random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT))
        end = (random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT))
        draw.line([start, end], fill=(150, 150, 150), width=1)

    # Точечный шум
    for _ in range(200):
        xy = (random.randint(0, IMAGE_WIDTH), random.randint(0, IMAGE_HEIGHT))
        draw.point(xy, fill=(random.randint(100, 200),) * 3)

    # Лёгкое размытие сглаживает края символов
    image = image.filter(ImageFilter.SMOOTH)

    # Сохраняем в память, а не на диск — картинка одноразовая
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def create_captcha() -> dict:
    """
    Создаёт новую капчу.

    Возвращает ключ и картинку в формате data URI —
    её можно вставить прямо в <img src="...">, без отдельного запроса.
    """
    code = _generate_code()
    key = uuid.uuid4().hex

    # Храним код в верхнем регистре: сравнение будет без учёта регистра
    cache.set(f'{CACHE_PREFIX}{key}', code.upper(), timeout=CAPTCHA_TTL)

    image_bytes = _draw_image(code)
    image_base64 = base64.b64encode(image_bytes).decode()

    return {
        'captcha_key': key,
        'captcha_image': f'data:image/png;base64,{image_base64}',
    }


def validate_captcha(key: str, value: str) -> bool:
    """
    Проверяет введённый код.

    Капча одноразовая: после проверки ключ удаляется из кеша,
    независимо от результата. Иначе один разгаданный код
    можно было бы использовать для сотни запросов.
    """
    if not key or not value:
        return False

    cache_key = f'{CACHE_PREFIX}{key}'
    stored_code = cache.get(cache_key)

    # Удаляем сразу: одна капча — одна попытка
    cache.delete(cache_key)

    if stored_code is None:
        return False  # ключ не найден или истёк срок

    return stored_code == value.strip().upper()