<script setup>
// Таблица заглавных комментариев с сортировкой.
//
// Клик по заголовку меняет поле сортировки, повторный клик
// по тому же полю переключает направление.

import { ref } from 'vue'

import { useCommentsStore } from '@/stores/comments'
import CommentThread from './CommentThread.vue'

const emit = defineEmits(['open-attachment'])

const store = useCommentsStore()

// id веток, которые пользователь раскрыл
const expandedIds = ref(new Set())

const columns = [
  { field: 'user_name', label: 'User Name' },
  { field: 'email', label: 'E-mail' },
  { field: 'created_at', label: 'Дата добавления' },
]

function toggleThread(id) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
  // Set не реактивен сам по себе — пересоздаём, чтобы Vue заметил изменение
  expandedIds.value = new Set(expandedIds.value)
}

function sortIcon(field) {
  if (store.ordering !== field) return '↕'
  return store.direction === 'asc' ? '↑' : '↓'
}

function formatDate(isoString) {
  return new Date(isoString).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Краткий текст для строки таблицы: теги убираем,
 * длинный текст обрезаем — полный виден при раскрытии ветки.
 */
function shortText(html) {
  const text = html.replace(/<[^>]*>/g, '')
  return text.length > 80 ? text.slice(0, 80) + '…' : text
}
</script>

<template>
  <div class="table-wrapper">
    <table class="table">
      <thead>
        <tr>
          <th
            v-for="column in columns"
            :key="column.field"
            class="table__sortable"
            @click="store.setSorting(column.field)"
          >
            {{ column.label }}
            <span class="table__icon">{{ sortIcon(column.field) }}</span>
          </th>
          <th>Сообщение</th>
          <th class="table__narrow">Ответы</th>
        </tr>
      </thead>

      <tbody>
        <template v-for="comment in store.comments" :key="comment.id">
          <tr class="table__row" @click="toggleThread(comment.id)">
            <td>
              <span class="table__expand">
                {{ expandedIds.has(comment.id) ? '▾' : '▸' }}
              </span>
              {{ comment.user_name }}
            </td>
            <td class="muted">{{ comment.email }}</td>
            <td class="muted">{{ formatDate(comment.created_at) }}</td>
            <td>
              {{ shortText(comment.text) }}
              <span v-if="comment.has_attachment" title="Есть вложение">📎</span>
            </td>
            <td class="table__narrow">{{ comment.replies_count }}</td>
          </tr>

          <tr v-if="expandedIds.has(comment.id)">
            <td colspan="5" class="table__thread-cell">
              <CommentThread
                :comment-id="comment.id"
                @open-attachment="emit('open-attachment', $event)"
              />
            </td>
          </tr>
        </template>
      </tbody>
    </table>

    <p v-if="!store.hasComments && !store.isLoading" class="muted empty">
      Пока нет ни одного комментария
    </p>
  </div>
</template>

<style scoped>
.table-wrapper {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  overflow: hidden;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table th {
  padding: 12px var(--spacing);
  text-align: left;
  font-weight: 500;
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
}

.table__sortable {
  cursor: pointer;
  user-select: none;
}

.table__sortable:hover {
  color: var(--color-text);
}

.table__icon {
  margin-left: 4px;
  opacity: 0.6;
}

.table td {
  padding: 12px var(--spacing);
  border-bottom: 1px solid var(--color-border);
}

.table__row {
  cursor: pointer;
}

.table__row:hover td {
  background: rgba(255, 255, 255, 0.02);
}

.table__expand {
  display: inline-block;
  width: 16px;
  color: var(--color-text-muted);
}

.table__narrow {
  width: 80px;
  text-align: center;
}

.table__thread-cell {
  padding: 0;
}

.empty {
  padding: calc(var(--spacing) * 2);
  text-align: center;
}

/* На узких экранах таблица прокручивается по горизонтали,
   вместо того чтобы ломать вёрстку */
@media (max-width: 700px) {
  .table-wrapper {
    overflow-x: auto;
  }

  .table {
    min-width: 600px;
  }
}
</style>