// Хранилище комментариев (Pinia).
//
// Состояние живёт здесь, а не внутри компонентов: список нужен
// и таблице, и форме, и обработчику WebSocket. Хранить его
// в одном месте проще, чем передавать между компонентами.

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

import { commentsApi } from '@/api/comments'

export const useCommentsStore = defineStore('comments', () => {
  // --- Состояние ---

  const comments = ref([])
  const totalCount = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(25)

  const ordering = ref('created_at')
  const direction = ref('desc')

  const isLoading = ref(false)
  const error = ref(null)

  // --- Вычисляемые значения ---

  const totalPages = computed(() =>
    Math.ceil(totalCount.value / pageSize.value) || 1,
  )

  const hasComments = computed(() => comments.value.length > 0)

  // --- Действия ---

  /**
   * Загружает страницу комментариев с текущими параметрами сортировки.
   */
  async function fetchComments() {
    isLoading.value = true
    error.value = null

    try {
      const data = await commentsApi.getList({
        page: currentPage.value,
        ordering: ordering.value,
        direction: direction.value,
      })

      comments.value = data.results
      totalCount.value = data.count
    } catch (err) {
      error.value = err.message || 'Не удалось загрузить комментарии'
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Меняет сортировку.
   * Повторный клик по тому же полю переключает направление.
   */
  function setSorting(field) {
    if (ordering.value === field) {
      direction.value = direction.value === 'asc' ? 'desc' : 'asc'
    } else {
      ordering.value = field
      direction.value = 'desc'
    }

    currentPage.value = 1
    fetchComments()
  }

  function setPage(page) {
    if (page < 1 || page > totalPages.value) return
    currentPage.value = page
    fetchComments()
  }

  /**
   * Добавляет комментарий, пришедший по WebSocket.
   *
   * Вставляем только заглавные комментарии и только на первой
   * странице при сортировке по умолчанию — иначе новая запись
   * нарушила бы текущий порядок на экране.
   */
  function addFromWebSocket(comment) {
    if (comment.parent !== null) {
      // Ответ: увеличиваем счётчик у родителя, если он на экране
      const parent = comments.value.find((c) => c.id === comment.parent)
      if (parent) {
        parent.replies_count += 1
      }
      return
    }

    const isDefaultView =
      currentPage.value === 1 &&
      ordering.value === 'created_at' &&
      direction.value === 'desc'

    if (!isDefaultView) {
      // Не на той странице — просто обновляем счётчик
      totalCount.value += 1
      return
    }

    // Защита от дубля: тот же комментарий мог прийти
    // и в ответе на создание, и по WebSocket
    if (comments.value.some((c) => c.id === comment.id)) return

    comments.value.unshift({ ...comment, replies_count: 0, has_attachment: false })
    totalCount.value += 1

    // Держим на странице ровно pageSize записей
    if (comments.value.length > pageSize.value) {
      comments.value.pop()
    }
  }

  return {
    comments,
    totalCount,
    currentPage,
    pageSize,
    ordering,
    direction,
    isLoading,
    error,
    totalPages,
    hasComments,
    fetchComments,
    setSorting,
    setPage,
    addFromWebSocket,
  }
})