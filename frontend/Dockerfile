# Образ для разработки фронтенда.
# Production-сборку сделаем отдельно на шаге деплоя.
FROM node:22-alpine

WORKDIR /app

# Сначала только файлы зависимостей — Docker закеширует слой,
# и npm install не будет повторяться при каждом изменении кода
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

# --host обязателен: без него сервер слушает только внутри контейнера
CMD ["npm", "run", "dev", "--", "--host"]