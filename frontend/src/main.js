// Точка входа приложения: подключаем плагины и монтируем Vue.

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import './styles/main.scss'

const app = createApp(App)

// Pinia — хранилище состояния, доступное всем компонентам
app.use(createPinia())

app.mount('#app')