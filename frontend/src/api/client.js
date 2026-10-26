// HTTP-клиент для общения с backend.
// Все запросы к API идут через него — настройки в одном месте.

import axios from 'axios'

const client = axios.create({
  // Относительный путь: при разработке Vite проксирует на Django,
  // в продакшене nginx направит на backend. Адрес менять не придётся.
  baseURL: '/api',
  timeout: 15000,
  headers: {
    Accept: 'application/json',
  },
})

// Перехватчик ответов: обрабатывает ошибки централизованно,
// чтобы не писать одинаковый try/catch в каждом компоненте
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // Ошибки валидации от DRF приходят как объект:
    // { "text": ["Не все теги закрыты"], "email": ["..."] }
    if (error.response?.status === 400) {
      return Promise.reject({
        type: 'validation',
        errors: error.response.data,
      })
    }

    if (error.response?.status === 404) {
      return Promise.reject({
        type: 'notFound',
        message: 'Запрашиваемые данные не найдены',
      })
    }

    if (error.response?.status >= 500) {
      return Promise.reject({
        type: 'server',
        message: 'Ошибка сервера. Попробуйте позже',
      })
    }

    // Запрос не дошёл до сервера: нет сети или истёк timeout
    if (!error.response) {
      return Promise.reject({
        type: 'network',
        message: 'Не удалось связаться с сервером',
      })
    }

    return Promise.reject({
      type: 'unknown',
      message: 'Произошла непредвиденная ошибка',
    })
  },
)

export default client