<script setup>

import { onMounted } from 'vue'

import { useCommentsStore } from '@/stores/comments'

const store = useCommentsStore()

// onMounted срабатывает после появления компонента на странице
onMounted(() => {
  store.fetchComments()
})
</script>

<template>
  <main>
    <h1>Комментарии</h1>

    <p v-if="store.isLoading">Загрузка…</p>

    <p v-else-if="store.error" class="error">{{ store.error }}</p>

    <template v-else>
      <p class="muted">Всего заглавных комментариев: {{ store.totalCount }}</p>

      <ul>
        <li v-for="comment in store.comments" :key="comment.id">
          <strong>{{ comment.user_name }}</strong>
          <span class="muted"> · {{ comment.email }}</span>
          <p>{{ comment.text }}</p>
        </li>
      </ul>
    </template>
  </main>
</template>

<style scoped>
h1 {
  margin-bottom: var(--spacing);
}

ul {
  list-style: none;
  margin-top: var(--spacing);
}

li {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--spacing);
  margin-bottom: 12px;
}

.muted {
  color: var(--color-text-muted);
  font-size: 14px;
}

.error {
  color: var(--color-danger);
}
</style>