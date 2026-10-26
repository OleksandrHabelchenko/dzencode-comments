// Методы работы с комментариями.
// Компоненты вызывают их и не знают деталей HTTP-запросов.

import client from './client'

export const commentsApi = {
  /**
   * Список заглавных комментариев с пагинацией и сортировкой.
   * @param {Object} params - page, ordering, direction
   */
  async getList(params = {}) {
    const { data } = await client.get('/comments/', { params })
    return data
  },

  /**
   * Один комментарий со всем деревом ответов.
   */
  async getThread(id) {
    const { data } = await client.get(`/comments/${id}/`)
    return data
  },

  /**
   * Создание комментария.
   *
   * Отправляем FormData, а не JSON: только так можно
   * приложить файл в одном запросе с остальными полями.
   */
  async create(payload) {
    const formData = new FormData()

    Object.entries(payload).forEach(([key, value]) => {
      // Пустые необязательные поля не отправляем,
      // иначе backend получит строку 'null' вместо отсутствия значения
      if (value !== null && value !== undefined && value !== '') {
        formData.append(key, value)
      }
    })

    const { data } = await client.post('/comments/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  /**
   * Новая капча: ключ и картинка в формате data URI.
   */
  async getCaptcha() {
    const { data } = await client.get('/comments/captcha/')
    return data
  },
}