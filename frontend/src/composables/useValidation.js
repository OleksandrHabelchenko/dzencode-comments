// Правила валидации полей формы.
//
// Вынесены отдельно от компонента: те же правила понадобятся
// при редактировании и в тестах. Повторяют серверную валидацию —
// клиент даёт быструю подсказку, сервер остаётся источником истины.

// Латинские буквы, цифры и пробелы между ними.
// Регулярка совпадает с валидатором в модели Django.
const USER_NAME_PATTERN = /^[a-zA-Z0-9]+( [a-zA-Z0-9]+)*$/

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const URL_PATTERN = /^https?:\/\/.+/

// Теги, разрешённые в тексте сообщения
const ALLOWED_TAGS = ['a', 'code', 'i', 'strong']

export const rules = {
  userName(value) {
    if (!value?.trim()) return 'Укажите имя пользователя'
    if (value.length > 50) return 'Не больше 50 символов'
    if (!USER_NAME_PATTERN.test(value)) {
      return 'Только латинские буквы, цифры и пробелы'
    }
    return null
  },

  email(value) {
    if (!value?.trim()) return 'Укажите e-mail'
    if (!EMAIL_PATTERN.test(value)) return 'Некорректный формат e-mail'
    return null
  },

  homePage(value) {
    // Необязательное поле: пустое значение допустимо
    if (!value?.trim()) return null
    if (!URL_PATTERN.test(value)) {
      return 'Адрес должен начинаться с http:// или https://'
    }
    return null
  },

  text(value) {
    if (!value?.trim()) return 'Введите текст сообщения'
    if (value.length > 10000) return 'Не больше 10000 символов'

    const tagError = validateTags(value)
    if (tagError) return tagError

    return null
  },

  captcha(value) {
    if (!value?.trim()) return 'Введите код с картинки'
    return null
  },
}

/**
 * Проверяет теги в тексте: разрешённые ли они,
 * закрыты ли и правильно ли вложены.
 *
 * Разбираем текст стеком: открывающий тег кладём в стек,
 * закрывающий должен совпасть с последним открытым.
 */
export function validateTags(text) {
  const tagRegex = /<\/?\s*([a-zA-Z][a-zA-Z0-9]*)[^>]*>/g
  const stack = []
  let match

  while ((match = tagRegex.exec(text)) !== null) {
    const fullTag = match[0]
    const tagName = match[1].toLowerCase()

    if (!ALLOWED_TAGS.includes(tagName)) {
      return `Тег <${tagName}> запрещён. Разрешены: <a>, <code>, <i>, <strong>`
    }

    const isClosing = fullTag.startsWith('</')

    if (isClosing) {
      if (stack.length === 0) {
        return `Закрывающий тег </${tagName}> без открывающего`
      }
      const last = stack.pop()
      if (last !== tagName) {
        return `Теги закрыты в неправильном порядке: ожидался </${last}>`
      }
    } else {
      stack.push(tagName)
    }
  }

  if (stack.length > 0) {
    return `Не закрыт тег <${stack[stack.length - 1]}>`
  }

  return null
}

/**
 * Проверяет все поля разом.
 * Возвращает объект с ошибками: пустой, если всё в порядке.
 */
export function validateForm(form) {
  const errors = {}

  const userNameError = rules.userName(form.user_name)
  if (userNameError) errors.user_name = userNameError

  const emailError = rules.email(form.email)
  if (emailError) errors.email = emailError

  const homePageError = rules.homePage(form.home_page)
  if (homePageError) errors.home_page = homePageError

  const textError = rules.text(form.text)
  if (textError) errors.text = textError

  const captchaError = rules.captcha(form.captcha_value)
  if (captchaError) errors.captcha_value = captchaError

  return errors
}