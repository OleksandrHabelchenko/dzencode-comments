<script setup>
// Поле капчи: картинка с кодом, поле ввода и кнопка обновления.
//
// Клик по картинке открывает её увеличенной — если код
// трудно разобрать в мелком размере.

import { ref, watch, onMounted, onUnmounted } from 'vue'

import { commentsApi } from '@/api/comments'

defineProps({
  modelValue: { type: String, default: '' },
  error: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue', 'update:captchaKey'])

const image = ref('')
const isLoading = ref(false)
const loadError = ref('')
const isZoomed = ref(false)

/**
 * Запрашивает новую капчу.
 * Старый ключ становится недействительным — он одноразовый.
 */
async function refresh() {
  isLoading.value = true
  loadError.value = ''
  isZoomed.value = false

  try {
    const data = await commentsApi.getCaptcha()
    image.value = data.captcha_image
    emit('update:captchaKey', data.captcha_key)
    emit('update:modelValue', '')
  } catch {
    loadError.value = 'Не удалось загрузить капчу'
  } finally {
    isLoading.value = false
  }
}

function onKeydown(event) {
  if (event.key === 'Escape') {
    isZoomed.value = false
  }
}

// Пока открыта увеличенная картинка, страница под ней
// не должна прокручиваться — то же поведение, что у лайтбокса
watch(isZoomed, (value) => {
  if (value) {
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', onKeydown)
  } else {
    document.body.style.overflow = ''
    document.removeEventListener('keydown', onKeydown)
  }
})

// Если компонент исчезнет с открытой картинкой,
// прокрутка осталась бы заблокированной навсегда
onUnmounted(() => {
  document.body.style.overflow = ''
  document.removeEventListener('keydown', onKeydown)
})

// Родительский компонент вызывает refresh() после отправки формы
defineExpose({ refresh })

onMounted(refresh)
</script>

<template>
  <div class="captcha">
    <label for="captcha">Код с картинки *</label>

    <div class="captcha__row">
      <div
        class="captcha__image"
        title="Нажмите, чтобы увеличить"
        @click="isZoomed = true"
      >
        <img v-if="image" :src="image" alt="Код с картинки" />
        <span v-else-if="isLoading" class="muted">Загрузка…</span>
        <span v-else-if="loadError" class="error">{{ loadError }}</span>
      </div>

      <button
        type="button"
        class="captcha__refresh"
        :disabled="isLoading"
        title="Обновить картинку"
        @click="refresh"
      >
        ↻
      </button>

      <input
        id="captcha"
        :value="modelValue"
        type="text"
        maxlength="5"
        autocomplete="off"
        placeholder="Введите код"
        :class="{ 'has-error': error }"
        @input="emit('update:modelValue', $event.target.value)"
      />
    </div>

    <span v-if="error" class="error">{{ error }}</span>

    <!-- Увеличенная картинка поверх страницы.
         Teleport выносит её из формы, чтобы не зависеть
         от overflow и z-index родительских элементов -->
    <Teleport to="body">
      <Transition name="zoom">
        <div v-if="isZoomed" class="captcha-zoom" @click="isZoomed = false">
          <img :src="image" alt="Код с картинки, увеличено" />
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.captcha__row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
}

.captcha__image {
  width: 180px;
  height: 68px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  cursor: zoom-in;
  transition: border-color 0.2s;
}

.captcha__image:hover {
  border-color: var(--color-accent);
}

.captcha__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.captcha__refresh {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  font-size: 20px;
  color: var(--color-text);
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: border-color 0.2s;
}

.captcha__refresh:hover:not(:disabled) {
  border-color: var(--color-accent);
}

.captcha__refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.captcha__row input {
  flex: 0 1 280px;
  font-size: 18px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
</style>

<style>
/* Не scoped: элемент вынесен через Teleport в body
   и стили со scoped до него бы не дошли */
.captcha-zoom {
  position: fixed;
  inset: 0;
  z-index: 1100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(4px);
  cursor: zoom-out;
}

.captcha-zoom img {
  /* Картинка маленькая, увеличиваем втрое.
     image-rendering сохраняет чёткость при масштабировании */
  width: 480px;
  max-width: 90vw;
  height: auto;
  border-radius: var(--radius);
  image-rendering: -webkit-optimize-contrast;
}

.zoom-enter-active,
.zoom-leave-active {
  transition: opacity 0.2s;
}

.zoom-enter-from,
.zoom-leave-to {
  opacity: 0;
}
</style>
