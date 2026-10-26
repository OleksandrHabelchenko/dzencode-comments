<script setup>
// Ветка комментариев: заглавный комментарий со всеми ответами.
//
// Дерево загружается по требованию, когда пользователь раскрывает ветку


import { ref } from 'vue'

import { commentsApi } from '@/api/comments'
import CommentItem from './CommentItem.vue'

const props = defineProps({
  commentId: { type: Number, required: true },
})

const emit = defineEmits(['open-attachment'])

const thread = ref(null)
const isLoading = ref(false)
const error = ref('')

async function load() {
  isLoading.value = true
  error.value = ''

  try {
    thread.value = await commentsApi.getThread(props.commentId)
  } catch (err) {
    error.value = err.message || 'Не удалось загрузить ветку'
  } finally {
    isLoading.value = false
  }
}

// Родитель вызывает load() при раскрытии ветки
defineExpose({ load })

load()
</script>

<template>
  <div class="thread">
    <p v-if="isLoading" class="muted">Загрузка ветки…</p>
    <p v-else-if="error" class="error">{{ error }}</p>

    <CommentItem
      v-else-if="thread"
      :comment="thread"
      @reply-created="load"
      @open-attachment="emit('open-attachment', $event)"
    />
  </div>
</template>

<style scoped>
.thread {
  padding: var(--spacing);
  background: var(--color-bg);
  border-top: 1px solid var(--color-border);
}
</style>