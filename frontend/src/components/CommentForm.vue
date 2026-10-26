<script setup>
// Форма добавления комментария.
//
// Используется и для заглавных комментариев, и для ответов:
// в режиме ответа получает parentId и отличается только заголовком.

import { ref, reactive, computed } from 'vue'

import { commentsApi } from '@/api/comments'
import { validateForm } from '@/composables/useValidation'
import CaptchaField from './CaptchaField.vue'
import TagToolbar from './TagToolbar.vue'

const props = defineProps({
  // id родительского комментария, если это ответ
  parentId: { type: Number, default: null },
})

const emit = defineEmits(['created', 'cancel'])

const form = reactive({
  user_name: '',
  email: '',
  home_page: '',
  text: '',
  captcha_value: '',
})

const captchaKey = ref('')
const attachmentFile = ref(null)
const attachmentName = ref('')

const errors = reactive({})
const serverError = ref('')
const isSubmitting = ref(false)

const showPreview = ref(false)
const textareaRef = ref(null)
const captchaRef = ref(null)

const isReply = computed(() => props.parentId !== null)

/**
 * Текст с применёнными тегами для предпросмотра.
 *
 * Экранируем всё, кроме разрешённых тегов: так превью показывает
 * результат и не даёт выполнить чужой скрипт прямо в браузере.
 */
const previewHtml = computed(() => {
  const escaped = form.text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Возвращаем обратно только разрешённые теги
  return escaped
    .replace(/&lt;(\/?)(i|strong|code)&gt;/g, '<$1$2>')
    .replace(/&lt;a href="([^"]*)"(?: title="([^"]*)")?&gt;/g,
      '<a href="$1" title="$2" target="_blank" rel="noopener">')
    .replace(/&lt;\/a&gt;/g, '</a>')
    .replace(/\n/g, '<br>')
})

function clearError(field) {
  delete errors[field]
  serverError.value = ''
}

/**
 * Выбор файла. Проверяем тип и размер до отправки —
 * пользователь узнает об ошибке сразу, а не после загрузки.
 */
function onFileChange(event) {
  const file = event.target.files[0]
  clearError('attachment_file')

  if (!file) {
    attachmentFile.value = null
    attachmentName.value = ''
    return
  }

  const isImage = ['image/jpeg', 'image/png', 'image/gif'].includes(file.type)
  const isText = file.type === 'text/plain' || file.name.toLowerCase().endsWith('.txt')

  if (!isImage && !isText) {
    errors.attachment_file = 'Разрешены изображения (JPG, PNG, GIF) и файлы TXT'
    event.target.value = ''
    return
  }

  if (isText && file.size > 100 * 1024) {
    errors.attachment_file = 'Текстовый файл не должен превышать 100 КБ'
    event.target.value = ''
    return
  }

  attachmentFile.value = file
  attachmentName.value = file.name
}

function removeFile() {
  attachmentFile.value = null
  attachmentName.value = ''
  clearError('attachment_file')
}

async function submit() {
  // Очищаем прошлые ошибки
  Object.keys(errors).forEach((key) => delete errors[key])
  serverError.value = ''

  const validationErrors = validateForm(form)
  if (Object.keys(validationErrors).length > 0) {
    Object.assign(errors, validationErrors)
    return
  }

  isSubmitting.value = true

  try {
    const comment = await commentsApi.create({
      ...form,
      parent: props.parentId,
      captcha_key: captchaKey.value,
      attachment_file: attachmentFile.value,
    })

    // Сбрасываем форму, но оставляем имя и email —
    // пользователь, скорее всего, напишет ещё
    form.text = ''
    form.captcha_value = ''
    removeFile()
    showPreview.value = false
    captchaRef.value?.refresh()

    emit('created', comment)
  } catch (err) {
    if (err.type === 'validation') {
      // Ошибки от сервера приходят как { поле: ["текст ошибки"] }
      Object.entries(err.errors).forEach(([field, messages]) => {
        errors[field] = Array.isArray(messages) ? messages[0] : messages
      })
      // Капча одноразовая — после неудачи нужна новая
      captchaRef.value?.refresh()
    } else {
      serverError.value = err.message || 'Не удалось отправить комментарий'
    }
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <form class="form" @submit.prevent="submit">
    <h3 class="form__title">
      {{ isReply ? 'Ответить на комментарий' : 'Оставить комментарий' }}
    </h3>

    <div class="form__row">
      <div class="field">
        <label for="user_name">Имя пользователя *</label>
        <input
          id="user_name"
          v-model="form.user_name"
          type="text"
          maxlength="50"
          :class="{ 'has-error': errors.user_name }"
          @input="clearError('user_name')"
        />
        <span v-if="errors.user_name" class="error">{{ errors.user_name }}</span>
      </div>

      <div class="field">
        <label for="email">E-mail *</label>
        <input
          id="email"
          v-model="form.email"
          type="email"
          :class="{ 'has-error': errors.email }"
          @input="clearError('email')"
        />
        <span v-if="errors.email" class="error">{{ errors.email }}</span>
      </div>
    </div>

    <div class="field">
      <label for="home_page">Домашняя страница</label>
      <input
        id="home_page"
        v-model="form.home_page"
        type="url"
        placeholder="https://example.com"
        :class="{ 'has-error': errors.home_page }"
        @input="clearError('home_page')"
      />
      <span v-if="errors.home_page" class="error">{{ errors.home_page }}</span>
    </div>

    <div class="field">
      <label for="text">Текст сообщения *</label>

      <TagToolbar v-model="form.text" :textarea-ref="textareaRef" />

      <textarea
        id="text"
        ref="textareaRef"
        v-model="form.text"
        rows="6"
        :class="{ 'has-error': errors.text }"
        @input="clearError('text')"
      />
      <span v-if="errors.text" class="error">{{ errors.text }}</span>

      <button
        type="button"
        class="link-button"
        @click="showPreview = !showPreview"
      >
        {{ showPreview ? 'Скрыть предпросмотр' : 'Показать предпросмотр' }}
      </button>

      <div v-if="showPreview" class="preview">
        <span class="preview__label">Предпросмотр</span>
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="preview__content" v-html="previewHtml" />
      </div>
    </div>

    <div class="field">
      <label for="attachment">Прикрепить файл</label>
      <input
        id="attachment"
        type="file"
        accept="image/jpeg,image/png,image/gif,.txt"
        @change="onFileChange"
      />
      <div v-if="attachmentName" class="file-chip">
        <span>{{ attachmentName }}</span>
        <button type="button" @click="removeFile">✕</button>
      </div>
      <span v-if="errors.attachment_file" class="error">
        {{ errors.attachment_file }}
      </span>
    </div>

    <CaptchaField
      ref="captchaRef"
      v-model="form.captcha_value"
      :error="errors.captcha_value"
      @update:captcha-key="captchaKey = $event"
    />

    <p v-if="serverError" class="error server-error">{{ serverError }}</p>

    <div class="form__actions">
      <button type="submit" class="button-primary" :disabled="isSubmitting">
        {{ isSubmitting ? 'Отправка…' : 'Отправить' }}
      </button>

      <button
        v-if="isReply"
        type="button"
        class="button-secondary"
        @click="emit('cancel')"
      >
        Отмена
      </button>
    </div>
  </form>
</template>

<style scoped>
.form {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: calc(var(--spacing) * 1.5);
  margin-bottom: calc(var(--spacing) * 2);
}

.form__title {
  margin-bottom: var(--spacing);
  font-size: 18px;
}

.form__row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing);
}

@media (max-width: 600px) {
  .form__row {
    grid-template-columns: 1fr;
  }
}

.field {
  margin-bottom: var(--spacing);
}

.field label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: var(--color-text-muted);
}

.preview {
  margin-top: 12px;
  padding: 12px;
  background: var(--color-bg);
  border: 1px dashed var(--color-border);
  border-radius: 8px;
}

.preview__label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.preview__content :deep(code) {
  padding: 2px 6px;
  background: var(--color-surface);
  border-radius: 4px;
  font-family: monospace;
}

.preview__content :deep(a) {
  color: var(--color-accent);
}

.file-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 6px 10px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  font-size: 14px;
}

.file-chip button {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
}

.link-button {
  margin-top: 8px;
  padding: 0;
  background: none;
  border: none;
  color: var(--color-accent);
  font-size: 14px;
  cursor: pointer;
}

.form__actions {
  display: flex;
  gap: 12px;
  margin-top: calc(var(--spacing) * 1.5);
}

.server-error {
  margin-top: 12px;
}
</style>