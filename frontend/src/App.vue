<script setup>
// Главная страница приложения.
//
// Собирает вместе форму, таблицу комментариев и пагинацию,
// подписывается на обновления по WebSocket.

import { onMounted, ref } from 'vue'

import CommentForm from '@/components/CommentForm.vue'
import CommentTable from '@/components/CommentTable.vue'
import FileLightbox from '@/components/FileLightbox.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import VantaBackground from '@/components/VantaBackground.vue'
import { useWebSocket } from '@/composables/useWebSocket'
import { useCommentsStore } from '@/stores/comments'

const store = useCommentsStore()

// Вложение, открытое в модальном окне
const activeAttachment = ref(null)

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
  activeAttachment.value = attachment
}
</script>

<template>
  <!-- Анимированный фон на WebGL, позиционируется сам -->
  <VantaBackground />

  <main>
    <header class="page-header">
      <h1>Комментарии</h1>

      <!-- Индикатор соединения: зелёная точка при активном WebSocket -->
      <span
        class="status"
        :class="{ 'is-online': isConnected }"
        :title="isConnected ? 'Обновления в реальном времени' : 'Нет соединения'"
      />
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

    <FileLightbox
      :attachment="activeAttachment"
      @close="activeAttachment = null"
    />
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
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-danger);
  transition: background 0.3s, box-shadow 0.3s;
}

.status.is-online {
  background: var(--color-success);
  /* Свечение вокруг точки подчёркивает активное состояние */
  box-shadow: 0 0 0 4px rgba(74, 222, 128, 0.15);
}

.count {
  margin-bottom: 12px;
}
</style>
