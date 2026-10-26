<script setup>
// Временная страница: форма + простой список.
// Полноценный интерфейс с таблицей и деревом — на следующем шаге.

import { onMounted } from 'vue'

import CommentForm from '@/components/CommentForm.vue'
import { useCommentsStore } from '@/stores/comments'

const store = useCommentsStore()

onMounted(() => {
  store.fetchComments()
})

// После успешной отправки перезагружаем список,
// чтобы новый комментарий появился на экране
function onCreated() {
  store.fetchComments()
}
</script>

<template>
  <main>
    <h1>Комментарии</h1>

    <CommentForm @created="onCreated" />

    <p v-if="store.isLoading">Загрузка…</p>
    <p v-else-if="store.error" class="error">{{ store.error }}</p>

    <template v-else>
      <p class="muted">Всего заглавных комментариев: {{ store.totalCount }}</p>

      <ul class="list">
        <li v-for="comment in store.comments" :key="comment.id">
          <strong>{{ comment.user_name }}</strong>
          <span class="muted"> · {{ comment.email }}</span>
          <p v-html="comment.text" />
        </li>
      </ul>
    </template>
  </main>
</template>

<style scoped>
h1 {
  margin-bottom: calc(var(--spacing) * 1.5);
}

.list {
  list-style: none;
  margin-top: var(--spacing);
}

.list li {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--spacing);
  margin-bottom: 12px;
}
</style>