<script setup>
// Панель кнопок для вставки разрешённых HTML-тегов.
//
// Кнопка оборачивает выделенный текст в тег, а если ничего
// не выделено — вставляет пустую пару и ставит курсор внутрь.

const props = defineProps({
  // Ссылка на textarea, в который вставляем теги
  textareaRef: { type: Object, default: null },
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

// Теги по ТЗ. Для ссылки сразу готовый шаблон с атрибутами.
const tags = [
  { name: 'i', label: 'i', title: 'Курсив', open: '<i>', close: '</i>' },
  { name: 'strong', label: 'strong', title: 'Жирный', open: '<strong>', close: '</strong>' },
  { name: 'code', label: 'code', title: 'Код', open: '<code>', close: '</code>' },
  { name: 'a', label: 'a', title: 'Ссылка', open: '<a href="" title="">', close: '</a>' },
]

function insertTag(tag) {
  const textarea = props.textareaRef
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const value = props.modelValue

  const selected = value.slice(start, end)
  const before = value.slice(0, start)
  const after = value.slice(end)

  const inserted = `${tag.open}${selected}${tag.close}`
  emit('update:modelValue', before + inserted + after)

  // Возвращаем фокус и ставим курсор после вставленного тега.
  // nextTick не нужен: setTimeout(0) дожидается перерисовки DOM
  setTimeout(() => {
    textarea.focus()
    const cursorPosition = selected
      ? start + inserted.length
      : start + tag.open.length
    textarea.setSelectionRange(cursorPosition, cursorPosition)
  }, 0)
}
</script>

<template>
  <div class="toolbar">
    <button
      v-for="tag in tags"
      :key="tag.name"
      type="button"
      class="toolbar__button"
      :title="tag.title"
      @click="insertTag(tag)"
    >
      [{{ tag.label }}]
    </button>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}

.toolbar__button {
  padding: 6px 10px;
  font-family: monospace;
  font-size: 13px;
  background: var(--color-surface);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
}

.toolbar__button:hover {
  color: var(--color-text);
  border-color: var(--color-accent);
}
</style>