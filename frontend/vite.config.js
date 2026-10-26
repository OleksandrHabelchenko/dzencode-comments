// Конфигурация сборщика Vite.
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      // Псевдоним @ указывает на папку src.
      // Вместо '../../components/Button.vue' пишем '@/components/Button.vue'
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  server: {
    // host: true делает сервер доступным извне контейнера,
    // иначе он слушал бы только localhost внутри него
    host: true,
    port: 5173,

    proxy: {
      // Запросы к /api/ Vite сам перенаправляет на Django.
      // Для браузера всё приходит с одного адреса — проблема CORS
      // при разработке не возникает вовсе.
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      // Медиафайлы: загруженные картинки и текстовые файлы
      '/media': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      // WebSocket требует отдельной настройки: ws: true
      // переключает прокси в режим постоянного соединения
      '/ws': {
        target: 'ws://backend:8000',
        ws: true,
      },
    },
  },
})