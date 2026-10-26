<script setup>
// Поле капчи: картинка с кодом, поле ввода и кнопка обновления.
//
// Ключ капчи хранится в компоненте и передаётся наверх
// через v-model — форма отправляет его вместе с остальными полями.

import { ref, onMounted } from 'vue'

import { commentsApi } from '@/api/comments'

const props = defineProps({
  modelValue: { type: String, default: '' },
  error: { type: String, default: '' },
})

// Два события: введённый код и ключ капчи
const emit = defineEmits(['update:modelValue', 'update:captchaKey'])

const image = ref('')
const isLoading = ref(false)
const loadError = ref('')

/**
 * Запрашивает новую капчу.
 * Старый ключ становится недействительным — он одноразовый.
 */
async function refresh() {
  isLoading.value = true
  loadError.value = ''

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

// Родительский компонент вызывает refresh() после отправки формы
defineExpose({ refresh })

onMounted(refresh)
</script>

<template>
  <div class="captcha">
    <label for="captcha">Код с картинки *</label>

    <div class="captcha__row">
      <div class="captcha__image">
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
  width: 160px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.captcha__image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.captcha__refresh {
  width: 40px;
  height: 40px;
  font-size: 20px;
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  cursor: pointer;
}

.captcha__refresh:hover:not(:disabled) {
  border-color: var(--color-accent);
}

.captcha__row input {
  flex: 1;
  text-transform: uppercase;
}
</style>