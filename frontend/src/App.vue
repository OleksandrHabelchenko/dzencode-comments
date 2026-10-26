<script setup>
// Главная страница приложения.
//
// Собирает вместе форму, таблицу комментариев и пагинацию,
// подписывается на обновления по WebSocket.

import { onMounted } from 'vue'

import CommentForm from '@/components/CommentForm.vue'
import CommentTable from '@/components/CommentTable.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { useCommentsStore } from '@/stores/comments'

const store = useCommentsStore()

// Новые комментарии прилетают по WebSocket и попадают
// в список без перезагрузки страницы
const { isConnected } = useWebSocket('/ws/comments/', (message) => {
  if (message.type === 'comment.created') {
    store.addFromWebSocket(message.comment)
  }
})

onMounted(() => {
  store.fetchComments()
})

function onCommentCreated() {
  // Список обновится по WebSocket, но на случай
  // обрыва соединения перезагружаем его явно
  if (!isConnected.value) {
    store.fetchComments()
  }
}

function onOpenAttachment(attachment) {
  // Просмотр файлов с анимацией — следующий шаг
  window.open(attachment.file_url, '_blank')
}
</script>

<template>
  <main>
    <header class="page-header">
      <h1>Комментарии</h1>

      <span class="status" :class="{ 'is-online': isConnected }">
        {{ isConnected ? 'Обновления в реальном времени' : 'Нет соединения' }}
      </span>
    </header>

    <CommentForm @created="onCommentCreated" />

    <section>
      <p class="muted count">
        Заглавных комментариев: {{ store.totalCount }}
      </p>

      <p v-if="store.error" class="error">{{ store.error }}</p>

      <CommentTable @open-attachment="onOpenAttachment" />

      <PaginationBar />
    </section>
  </main>
</template>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: calc(var(--spacing) * 1.5);
}

.status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--color-text-muted);
}

.status::before {
  content: '';
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-danger);
}

.status.is-online::before {
  background: #3fb950;
}

.count {
  margin-bottom: 12px;
}
</style>