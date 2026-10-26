<script setup>
// Отображение прикреплённого файла.
//
// Картинка показывается превью, текстовый файл — ссылкой.

const props = defineProps({
  attachment: { type: Object, required: true },
})

const emit = defineEmits(['open'])

const isImage = props.attachment.file_type === 'image'
</script>

<template>
  <div class="attachment">
    <img
      v-if="isImage"
      :src="attachment.file_url"
      :alt="attachment.original_name"
      :width="attachment.width"
      :height="attachment.height"
      loading="lazy"
      @click="emit('open', attachment)"
    />

    <button v-else type="button" class="attachment__file" @click="emit('open', attachment)">
      <span class="attachment__icon">📄</span>
      <span>{{ attachment.original_name }}</span>
    </button>
  </div>
</template>

<style scoped>
.attachment {
  margin-top: 12px;
}

.attachment img {
  max-width: 320px;
  height: auto;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  cursor: pointer;
  transition: opacity 0.2s;
}

.attachment img:hover {
  opacity: 0.85;
}

.attachment__file {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-bg);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
}

.attachment__file:hover {
  border-color: var(--color-accent);
}

.attachment__icon {
  font-size: 18px;
}
</style>