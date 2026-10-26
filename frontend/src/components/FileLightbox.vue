<script setup>
// Модальное окно для просмотра вложений.
//
// Картинка показывается в полном размере, текстовый файл
// подгружается и выводится как текст. Закрытие по Escape,
// клику на фон или крестику.

import { ref, watch, onUnmounted } from 'vue'

const props = defineProps({
  // Вложение для показа; null означает, что окно закрыто
  attachment: { type: Object, default: null },
})

const emit = defineEmits(['close'])

const textContent = ref('')
const isLoadingText = ref(false)
const loadError = ref('')

/**
 * Загружает содержимое текстового файла.
 *
 * Картинку браузер покажет сам по ссылке, а текст нужно
 * прочитать и вывести — иначе файл просто скачается.
 */
async function loadTextFile(url) {
  isLoadingText.value = true
  loadError.value = ''
  textContent.value = ''

  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error()
    textContent.value = await response.text()
  } catch {
    loadError.value = 'Не удалось загрузить файл'
  } finally {
    isLoadingText.value = false
  }
}

function close() {
  emit('close')
}

function onKeydown(event) {
  if (event.key === 'Escape') close()
}

// Следим за сменой вложения: открываем окно, грузим текст,
// блокируем прокрутку страницы под модалкой
watch(
  () => props.attachment,
  (value) => {
    if (value) {
      document.addEventListener('keydown', onKeydown)
      // overflow: hidden не даёт фону прокручиваться,
      // пока открыто модальное окно
      document.body.style.overflow = 'hidden'

      if (value.file_type === 'text') {
        loadTextFile(value.file_url)
      }
    } else {
      document.removeEventListener('keydown', onKeydown)
      document.body.style.overflow = ''
      textContent.value = ''
    }
  },
)

// Если компонент исчезнет с открытым окном, прокрутка
// осталась бы заблокированной навсегда
onUnmounted(() => {
  document.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <!-- Teleport переносит окно в конец body: так оно
       не зависит от overflow и z-index родительских элементов -->
  <Teleport to="body">
    <Transition name="lightbox">
      <div v-if="attachment" class="lightbox" @click.self="close">
        <button type="button" class="lightbox__close" title="Закрыть" @click="close">
          ✕
        </button>

        <div class="lightbox__content">
          <img
            v-if="attachment.file_type === 'image'"
            :src="attachment.file_url"
            :alt="attachment.original_name"
            class="lightbox__image"
          />

          <div v-else class="lightbox__text">
            <p v-if="isLoadingText" class="muted">Загрузка…</p>
            <p v-else-if="loadError" class="error">{{ loadError }}</p>
            <pre v-else>{{ textContent }}</pre>
          </div>

          <footer class="lightbox__caption">
            <span>{{ attachment.original_name }}</span>
            <a
              :href="attachment.file_url"
              download
              class="lightbox__download"
            >
              Скачать
            </a>
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: calc(var(--spacing) * 2);
  /* Полупрозрачный фон с размытием: содержимое страницы
     остаётся видимым, но не отвлекает */
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
}

.lightbox__close {
  position: absolute;
  top: 20px;
  right: 24px;
  width: 40px;
  height: 40px;
  font-size: 20px;
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: background 0.2s;
}

.lightbox__close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.lightbox__content {
  max-width: 90vw;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lightbox__image {
  max-width: 100%;
  max-height: 75vh;
  object-fit: contain;
  border-radius: var(--radius);
}

.lightbox__text {
  max-height: 75vh;
  overflow: auto;
  padding: var(--spacing);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
}

.lightbox__text pre {
  white-space: pre-wrap;
  word-break: break-word;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.6;
}

.lightbox__caption {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing);
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.lightbox__download {
  color: var(--color-accent);
  text-decoration: none;
}

.lightbox__download:hover {
  text-decoration: underline;
}

/* Анимация появления: фон проявляется,
   содержимое подъезжает снизу с лёгким масштабированием */
.lightbox-enter-active,
.lightbox-leave-active {
  transition: opacity 0.25s ease;
}

.lightbox-enter-active .lightbox__content,
.lightbox-leave-active .lightbox__content {
  transition: transform 0.25s cubic-bezier(0.34, 1.3, 0.64, 1);
}

.lightbox-enter-from,
.lightbox-leave-to {
  opacity: 0;
}

.lightbox-enter-from .lightbox__content,
.lightbox-leave-to .lightbox__content {
  transform: scale(0.94) translateY(12px);
}

/* Уважаем системную настройку: пользователям, которым
   анимации мешают, показываем окно без движения */
@media (prefers-reduced-motion: reduce) {
  .lightbox-enter-active .lightbox__content,
  .lightbox-leave-active .lightbox__content {
    transition: none;
  }
}
</style>