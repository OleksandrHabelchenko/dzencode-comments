# SPA «Комментарии»

Одностраничное приложение для древовидных комментариев с вложениями,
капчей и обновлением в реальном времени.

Тестовое задание для dZENcode, уровень **Junior+**.

**Демо:** https://2-31-113-91.sslip.io

---

## Стек

**Backend:** Python 3.12, Django 5.2, Django REST Framework, Daphne (ASGI)
**База данных:** MySQL 8.0
**Очередь и кеш:** Redis 7, Celery
**Реальное время:** Django Channels (WebSocket)
**Frontend:** Vue 3 (Composition API), Pinia, Vite, Axios
**Инфраструктура:** Docker, Docker Compose, nginx, Let's Encrypt

---

## Возможности

### Комментарии

- Древовидная структура неограниченной вложенности: ответить можно
  на любой комментарий, включая ответ на ответ
- Заглавные комментарии выводятся таблицей с сортировкой по
  User Name, E-mail и дате добавления — в обе стороны
- Сортировка по умолчанию LIFO: новые сверху
- Пагинация по 25 записей на страницу
- Ветка ответов загружается по требованию, при раскрытии строки

### Форма добавления

- Обязательные поля: User Name, E-mail, CAPTCHA, текст сообщения
- Необязательное поле: Home page в формате URL
- Валидация на стороне клиента и сервера
- Предпросмотр сообщения без перезагрузки страницы
- Панель кнопок для вставки разрешённых тегов: `[i] [strong] [code] [a]`

### CAPTCHA

- Изображение генерируется на сервере (Pillow): случайный код,
  помехи в виде линий и точечного шума, лёгкое размытие
- Правильный ответ хранится в Redis и клиенту не передаётся
- Капча одноразовая: ключ удаляется после первой же проверки
- Срок жизни 10 минут
- Клик по картинке открывает её увеличенной

### Вложения

- Изображения: JPG, PNG, GIF. Файлы больше 320×240 пропорционально
  уменьшаются алгоритмом LANCZOS
- Текстовые файлы: TXT до 100 КБ
- Тип файла определяется по содержимому, а не по расширению —
  переименованный исполняемый файл не пройдёт
- Просмотр в модальном окне с анимацией: изображение открывается
  в полном размере, текстовый файл выводится с сохранением форматирования

### Реальное время

- Новые комментарии появляются у всех открывших сайт без перезагрузки
- Автоматическое переподключение при обрыве связи с нарастающей
  задержкой от 1 до 30 секунд
- Периодический ping не даёт прокси разорвать бездействующее соединение

---

## Безопасность

**XSS.** Разрешены только четыре тега: `<a href="" title="">`, `<code>`,
`<i>`, `<strong>`. Текст очищается библиотекой `bleach` по белым спискам
тегов, атрибутов и протоколов — ссылка вида `javascript:alert(1)`
будет обезврежена. Для `<a>` разрешены только `href` и `title`.

**Валидность разметки.** Структура тегов проверяется XML-парсером `lxml`:
незакрытый тег и нарушенный порядок вложенности отклоняются с разными
сообщениями. Подстановка XML-сущностей отключена — защита от billion
laughs attack.

**SQL-инъекции.** Все запросы к базе идут через Django ORM, который
использует параметризованные запросы. Сырой SQL в проекте не применяется.

**Прочее.** Ограничение длины текста, лимиты на размер файлов, белый
список полей сортировки, фиксированный размер страницы, защитные
HTTP-заголовки и безопасные куки в продакшене.

---

## Инструменты уровня Junior+

| Требование | Реализация |
|---|---|
| **Queue** | Celery: сброс кеша после добавления комментария, уведомление автора родительского комментария. Повтор до трёх раз при сбое |
| **Cache** | Redis: кеш Django и хранилище капчи |
| **Events** | Сигналы Django `post_save` рассылают новый комментарий по WebSocket. Логика рассылки отделена от логики создания |
| **JWT** | `djangorestframework-simplejwt`: access 30 минут, refresh 7 дней, ротация с чёрным списком. Защищает административные действия |

Комментарии по заданию анонимные, поэтому публичные эндпоинты открыты.
JWT требуется для удаления комментария.

---

## Запуск для разработки

Нужен только Docker — Python, Node и MySQL на компьютер ставить не надо.

```bash
git clone https://github.com/OleksandrHabelchenko/dzencode-comments.git
cd dzencode-comments
```

Создай файл настроек:

```bash
cp .env.example .env
```

Открой `.env` и заполни три значения:

```
SECRET_KEY=любая_длинная_случайная_строка
DB_PASSWORD=любой_пароль
DB_ROOT_PASSWORD=любой_другой_пароль
```


Запусти:

```bash
docker compose up -d --build
```

Первый запуск занимает несколько минут: собираются образы и
инициализируется база. Дождись готовности базы:

```bash
docker compose ps
```

У сервиса `db` в колонке STATUS должно появиться `healthy`.

Примени миграции и создай администратора:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

Готово:

- Приложение — http://localhost:5173
- API — http://localhost:8000/api/comments/
- Админка — http://localhost:8000/admin

Остановить: `docker compose down`

### Тестовые данные

Для проверки пагинации и сортировки:

```bash
docker compose exec backend python manage.py seed_comments --count 60
```

Создаёт 60 заглавных комментариев со случайными ответами.

---

## Запуск в продакшене

```bash
git clone https://github.com/OleksandrHabelchenko/dzencode-comments.git
cd dzencode-comments
```

Создай `.env` с боевыми значениями:

```
DEBUG=False
SECRET_KEY=длинная_случайная_строка
ALLOWED_HOSTS=ваш_домен,localhost,127.0.0.1,backend

DB_NAME=comments_db
DB_USER=comments_user
DB_PASSWORD=пароль
DB_ROOT_PASSWORD=root_пароль
DB_HOST=db
DB_PORT=3306

REDIS_HOST=redis
REDIS_PORT=6379

CORS_ALLOWED_ORIGINS=https://ваш_домен
CSRF_TRUSTED_ORIGINS=https://ваш_домен
SECURE_COOKIES=True
NGINX_CONF=nginx-ssl.conf
```


`SECURE_COOKIES` ставится в `False`, если сайт работает по HTTP:
иначе браузер не отправит куки и формы не пройдут проверку.
`NGINX_CONF` выбирает конфигурацию nginx — без HTTPS укажи `nginx.conf`.

Запуск:

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

Миграции и сбор статики выполняются автоматически при старте контейнера.

### HTTPS

```bash
mkdir -p certbot/conf certbot/www
docker run --rm \
  -v $(pwd)/certbot/conf:/etc/letsencrypt \
  -v $(pwd)/certbot/www:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d ваш_домен --email ваш@email --agree-tos --no-eff-email
```

После выпуска сертификата укажи `NGINX_CONF=nginx-ssl.conf` в `.env`
и перезапусти nginx. Автопродление настраивается заданием в cron.

**Отличия продакшена от разработки:**

- Daphne вместо `runserver`
- Vue собран в статику, Vite не запускается
- nginx раздаёт статику и проксирует API, админку и WebSocket
- Наружу открыты только порты 80 и 443, база и Redis доступны лишь
  внутри сети Docker
- Код внутри образа, а не монтируется с диска

---

## Структура проекта

```
dzencode-comments/
├── backend/
│ ├── comments/
│ │ ├── models.py модели Comment и Attachment
│ │ ├── serializers.py сериализаторы DRF
│ │ ├── views.py эндпоинты API
│ │ ├── captcha.py генерация и проверка капчи
│ │ ├── text_validation.py проверка тегов, XHTML, защита от XSS
│ │ ├── file_validation.py обработка вложений, ресайз картинок
│ │ ├── tasks.py фоновые задачи Celery
│ │ ├── consumers.py обработчик WebSocket
│ │ ├── signals.py рассылка событий
│ │ ├── routing.py маршруты WebSocket
│ │ └── management/commands/
│ │ └── seed_comments.py генератор тестовых данных
│ └── config/
│ ├── settings.py
│ ├── urls.py HTTP-маршруты
│ ├── asgi.py точка входа ASGI
│ └── celery.py настройка Celery
├── frontend/
│ ├── Dockerfile образ для разработки
│ ├── Dockerfile.prod многоступенчатая сборка для продакшена
│ └── src/
│ ├── api/ слой работы с API
│ ├── components/ компоненты интерфейса
│ ├── composables/ валидация, WebSocket
│ ├── stores/ хранилище Pinia
│ └── styles/ глобальные стили
├── docker/
│ ├── nginx.conf конфигурация nginx без HTTPS
│ └── nginx-ssl.conf конфигурация с HTTPS
├── docs/
│ └── schema.sql схема БД для MySQL Workbench
├── docker-compose.yml окружение разработки
└── docker-compose.prod.yml окружение продакшена
```


---

## API

| Метод | Адрес | Назначение |
|---|---|---|
| GET | `/api/comments/` | Таблица заглавных комментариев. Параметры: `page`, `ordering`, `direction` |
| POST | `/api/comments/` | Создание комментария или ответа (multipart/form-data) |
| GET | `/api/comments/<id>/` | Комментарий со всем деревом ответов |
| DELETE | `/api/comments/<id>/delete/` | Удаление. Требует JWT администратора |
| GET | `/api/comments/captcha/` | Новая капча: ключ и изображение |
| POST | `/api/auth/token/` | Получение пары токенов по логину и паролю |
| POST | `/api/auth/token/refresh/` | Обновление access-токена |
| POST | `/api/auth/token/verify/` | Проверка токена |
| WS | `/ws/comments/` | Подписка на новые комментарии |

**Сортировка:** `?ordering=user_name&direction=asc`
Допустимые поля: `user_name`, `email`, `created_at`.
Направление: `asc`, `desc`. По умолчанию — `created_at` + `desc`.

---

## Схема базы данных

Файл `docs/schema.sql` снят командой `mysqldump` с рабочей базы и
открывается в MySQL Workbench:
**File → Import → Reverse Engineer MySQL Create Script**

### Comment

| Поле | Тип | Описание |
|---|---|---|
| id | BIGINT | Первичный ключ |
| parent_id | BIGINT NULL | Ссылка на родительский комментарий. NULL — заглавный |
| root_id | BIGINT NULL | Ссылка на корень ветки. Денормализация ради скорости |
| user_name | VARCHAR(50) | Имя пользователя |
| email | VARCHAR(254) | E-mail |
| home_page | VARCHAR(200) | Домашняя страница, необязательно |
| text | LONGTEXT | Текст сообщения |
| created_at | DATETIME | Дата добавления, индексирована |
| ip_address | CHAR(39) | IP клиента, заполняется сервером |
| user_agent | LONGTEXT | User-Agent браузера |

Поле `root_id` позволяет достать всех потомков ветки одним запросом
вместо рекурсивного обхода уровней.

### Attachment

| Поле | Тип | Описание |
|---|---|---|
| id | BIGINT | Первичный ключ |
| comment_id | BIGINT UNIQUE | Связь один-к-одному с комментарием |
| file | VARCHAR(100) | Путь к файлу |
| file_type | VARCHAR(10) | `image` или `text` |
| original_name | VARCHAR(255) | Исходное имя файла |
| width, height | INT NULL | Размеры изображения после обработки |
| uploaded_at | DATETIME | Дата загрузки |

---

## Ветвление в Git

- `main` — стабильная версия, то что развёрнуто
- `develop` — основная ветка разработки
- `feature/*` — отдельная ветка на каждую задачу

Каждая функциональность разрабатывалась в своей ветке и вливалась
в `develop` после проверки. Формат сообщений — Conventional Commits.
READMEEND