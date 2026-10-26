<script setup>
// Один комментарий в дереве.
//
// Компонент рекурсивный: внутри себя выводит ответы
// тем же компонентом, поэтому глубина вложенности не ограничена.

import { ref } from 'vue'

import AttachmentView from './AttachmentView.vue'
import CommentForm from './CommentForm.vue'

defineProps({
  comment: { type: Object, required: true },
  // Уровень вложенности: нужен, чтобы ограничить отступ
  // и не уехать за край экрана на глубоких ветках
  depth: { type: Number, default: 0 },
})

const emit = defineEmits(['reply-created', 'open-attachment'])

const showReplyForm = ref(false)

/**
 * Дата в читаемом виде: 26.10.2026, 14:30
 */
function formatDate(isoString) {
  return new Date(isoString).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function onReplyCreated(comment) {
  showReplyForm.value = false
  emit('reply-created', comment)
}
</script>

<template>
  <article class="comment" :style="{ marginLeft: `${Math.min(depth, 6) * 24}px` }">
    <div class="comment__card">
      <header class="comment__header">
        <span class="comment__author">{{ comment.user_name }}</span>
        <a
          v-if="comment.home_page"
          :href="comment.home_page"
          target="_blank"
          rel="noopener noreferrer"
          class="comment__link"
          title="Домашняя страница"
        >
          ↗
        </a>
        <span class="comment__date">{{ formatDate(comment.created_at) }}</span>
      </header>

      <!-- Текст уже очищен на сервере: разрешены только 4 тега -->
      <!-- eslint-disable-next-line vue/no-v-html -->
      <div class="comment__text" v-html="comment.text" />

      <AttachmentView
        v-if="comment.attachment"
        :attachment="comment.attachment"
        @open="emit('open-attachment', $event)"
      />

      <footer class="comment__footer">
        <button type="button" class="link-button" @click="showReplyForm = !showReplyForm">
          {{ showReplyForm ? 'Отмена' : 'Ответить' }}
        </button>
      </footer>
    </div>

    <CommentForm
      v-if="showReplyForm"
      :parent-id="comment.id"
      class="comment__reply-form"
      @created="onReplyCreated"
      @cancel="showReplyForm = false"
    />

    <!-- Рекурсия: каждый ответ выводится тем же компонентом -->
    <CommentItem
      v-for="reply in comment.replies"
      :key="reply.id"
      :comment="reply"
      :depth="depth + 1"
      @reply-created="emit('reply-created', $event)"
      @open-attachment="emit('open-attachment', $event)"
    />
  </article>
</template>

<style scoped>
.comment {
  position: relative;
  margin-top: 12px;
}

/* Вертикальная линия слева у вложенных комментариев —
   визуально связывает ответ с родителем */
.comment[style*='margin-left']::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--color-border);
}

.comment__card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: var(--spacing);
}

.comment__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.comment__author {
  font-weight: 600;
}

.comment__link {
  color: var(--color-accent);
  text-decoration: none;
  font-size: 14px;
}

.comment__date {
  margin-left: auto;
  font-size: 13px;
  color: var(--color-text-muted);
}

.comment__text {
  line-height: 1.6;
  word-break: break-word;
}

.comment__text :deep(code) {
  padding: 2px 6px;
  background: var(--color-bg);
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
}

.comment__text :deep(a) {
  color: var(--color-accent);
}

.comment__footer {
  margin-top: 12px;
}

.comment__reply-form {
  margin-top: 12px;
  margin-bottom: 0;
}
</style>