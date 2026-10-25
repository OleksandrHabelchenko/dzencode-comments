"""
Проверка и очистка текста комментария.

1. Разрешены только теги <a href="" title="">, <code>, <i>, <strong>
2. Теги должны быть закрыты, код — валидный XHTML
3. Защита от XSS

Порядок работы: сначала проверяем структуру (закрытие тегов),
потом очищаем от всего лишнего. Если сделать наоборот,
bleach молча починит незакрытый тег, и проверка ТЗ не сработает.
"""

import re

import bleach
from django.core.exceptions import ValidationError
from lxml import etree

# Разрешённые теги — строго по ТЗ, ничего сверх
ALLOWED_TAGS = ['a', 'code', 'i', 'strong']

# Разрешённые атрибуты: только у тега <a>, только href и title.
# Любой другой атрибут (onclick, style, onerror) будет удалён.
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
}

# Разрешённые протоколы в href.
# Без этого списка сработал бы javascript:alert(1) — классический XSS.
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

# Максимальная длина текста — защита от переполнения базы
MAX_TEXT_LENGTH = 10000


def _check_xhtml_validity(text: str) -> None:
    """
    Проверяет, что теги закрыты и правильно вложены.

    Текст оборачивается в фиктивный корневой элемент, потому что
    XML требует ровно один корень, а комментарий может начинаться
    с обычного текста или содержать несколько тегов подряд.

    Ошибку парсера переводим в понятное пользователю сообщение.
    """
    wrapped = f'<root>{text}</root>'

    try:
        # resolve_entities=False отключает подстановку XML-сущностей —
        # это защита от billion laughs attack (бомба из вложенных сущностей)
        parser = etree.XMLParser(resolve_entities=False)
        etree.fromstring(wrapped.encode('utf-8'), parser=parser)
    except etree.XMLSyntaxError as exc:
        message = str(exc).lower()

        if 'opening and ending tag mismatch' in message:
            # Парсер дошёл до нашей обёртки <root>, не встретив закрывающий тег —
            # значит пользователь его просто не поставил.
            # Если же в сообщении другой тег, перепутан порядок закрытия.
            if 'and root' in message:
                raise ValidationError(
                    'Не все теги закрыты. '
                    'Каждый открытый тег должен иметь закрывающий, например: '
                    '<strong>текст</strong>'
                )
            raise ValidationError(
                'Теги закрыты в неправильном порядке. '
                'Пример правильной вложенности: <strong><i>текст</i></strong>'
            )

        if 'premature end of data' in message:
            raise ValidationError(
                'Не все теги закрыты. Каждый открытый тег должен иметь закрывающий.'
            )

        raise ValidationError(
            'Текст содержит некорректную HTML-разметку. '
            'Проверьте, что все теги закрыты и правильно вложены.'
        )


def _check_only_allowed_tags(text: str) -> None:
    """
    Проверяет, что в тексте нет запрещённых тегов.

    Мы не просто молча вырезаем лишнее, а сообщаем об ошибке:
    пользователь должен понимать, почему его текст изменился.
    """
    # Находим имена всех тегов в тексте
    found_tags = set(re.findall(r'</?\s*([a-zA-Z][a-zA-Z0-9]*)', text))
    forbidden = found_tags - set(ALLOWED_TAGS)

    if forbidden:
        allowed_list = ', '.join(f'<{tag}>' for tag in ALLOWED_TAGS)
        forbidden_list = ', '.join(f'<{tag}>' for tag in sorted(forbidden))
        raise ValidationError(
            f'Запрещённые теги: {forbidden_list}. '
            f'Разрешены только: {allowed_list}'
        )


def clean_comment_text(text: str) -> str:
    """
    Полная обработка текста комментария.

    Возвращает безопасный текст, готовый к сохранению и выводу.
    Бросает ValidationError, если текст нарушает требования.
    """
    if not text or not text.strip():
        raise ValidationError('Текст сообщения не может быть пустым')

    text = text.strip()

    if len(text) > MAX_TEXT_LENGTH:
        raise ValidationError(
            f'Текст слишком длинный: максимум {MAX_TEXT_LENGTH} символов'
        )

    # Шаг 1: структура — все ли теги закрыты и правильно вложены
    _check_xhtml_validity(text)

    # Шаг 2: состав — нет ли запрещённых тегов
    _check_only_allowed_tags(text)

    # Шаг 3: очистка. Даже после двух проверок прогоняем через bleach —
    # он уберёт опасные атрибуты и протоколы, которые проверки пропустили.
    # strip=False означает, что оставшиеся запрещённые конструкции
    # будут экранированы (&lt;script&gt;), а не удалены молча.
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=False,
    )

    return cleaned