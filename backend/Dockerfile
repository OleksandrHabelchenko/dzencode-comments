# Образ для Django-приложения.
# Берём slim-версию Python: меньше размер, меньше лишнего внутри.
FROM python:3.12-slim

# Python не пишет .pyc файлы и не буферизует вывод —
# так логи сразу видны в консоли Docker.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Системные библиотеки, нужные для сборки mysqlclient.
# После установки чистим кеш apt, чтобы образ не раздувался.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая папка внутри контейнера
WORKDIR /app

# Сначала копируем только requirements.txt и ставим зависимости.
# Docker кеширует этот слой: пока файл не изменился,
# пересборка образа не будет заново качать пакеты.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Теперь копируем сам код проекта
COPY . .

# Порт, на котором внутри контейнера работает Django
EXPOSE 8000