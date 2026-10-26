<script setup>
// Постраничная навигация.
//
// Показываем не все страницы, а окно вокруг текущей:
// при сотне страниц полный список занял бы весь экран.

import { computed } from 'vue'

import { useCommentsStore } from '@/stores/comments'

const store = useCommentsStore()

// Сколько страниц показывать по бокам от текущей
const WINDOW_SIZE = 2

const pages = computed(() => {
  const total = store.totalPages
  const current = store.currentPage
  const result = []

  for (let i = 1; i <= total; i += 1) {
    const isEdge = i === 1 || i === total
    const isNearCurrent = Math.abs(i - current) <= WINDOW_SIZE

    if (isEdge || isNearCurrent) {
      result.push(i)
    } else if (result[result.length - 1] !== '…') {
      // Пропуск обозначаем многоточием, но только один раз подряд
      result.push('…')
    }
  }

  return result
})
</script>

<template>
  <nav v-if="store.totalPages > 1" class="pagination">
    <button
      type="button"
      class="pagination__button"
      :disabled="store.currentPage === 1"
      @click="store.setPage(store.currentPage - 1)"
    >
      ←
    </button>

    <template v-for="(page, index) in pages" :key="index">
      <span v-if="page === '…'" class="pagination__gap">…</span>

      <button
        v-else
        type="button"
        class="pagination__button"
        :class="{ 'is-active': page === store.currentPage }"
        @click="store.setPage(page)"
      >
        {{ page }}
      </button>
    </template>

    <button
      type="button"
      class="pagination__button"
      :disabled="store.currentPage === store.totalPages"
      @click="store.setPage(store.currentPage + 1)"
    >
      →
    </button>
  </nav>
</template>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: calc(var(--spacing) * 1.5);
}

.pagination__button {
  min-width: 36px;
  height: 36px;
  padding: 0 10px;
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.pagination__button:hover:not(:disabled):not(.is-active) {
  border-color: var(--color-accent);
}

.pagination__button.is-active {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: #fff;
}

.pagination__button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.pagination__gap {
  color: var(--color-text-muted);
  padding: 0 4px;
}
</style>