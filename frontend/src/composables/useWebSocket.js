// Подключение к WebSocket с автоматическим переподключением.
//
// Вынесено в composable: логика соединения не зависит от того,
// какой компонент её использует, и переиспользуется при необходимости.

import { ref, onMounted, onUnmounted } from 'vue'

// Пауза перед повторным подключением растёт при каждой неудаче,
// чтобы не долбить упавший сервер каждую секунду
const RECONNECT_BASE_DELAY = 1000
const RECONNECT_MAX_DELAY = 30000

// Интервал ping: держит соединение живым, иначе прокси
// может разорвать его как бездействующее
const PING_INTERVAL = 30000

export function useWebSocket(path, onMessage) {
  const isConnected = ref(false)

  let socket = null
  let reconnectAttempts = 0
  let reconnectTimer = null
  let pingTimer = null

  function buildUrl() {
    // На https сайте WebSocket тоже должен быть защищённым (wss),
    // иначе браузер заблокирует соединение
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${protocol}//${window.location.host}${path}`
  }

  function connect() {
    socket = new WebSocket(buildUrl())

    socket.onopen = () => {
      isConnected.value = true
      reconnectAttempts = 0
      startPing()
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        // Ответы на ping обрабатывать не нужно
        if (data.type === 'pong') return
        onMessage(data)
      } catch {
        // Некорректное сообщение игнорируем:
        // падать из-за одного битого пакета незачем
      }
    }

    socket.onclose = () => {
      isConnected.value = false
      stopPing()
      scheduleReconnect()
    }

    socket.onerror = () => {
      socket?.close()
    }
  }

  function scheduleReconnect() {
    // Экспоненциальная задержка: 1с, 2с, 4с, 8с… но не больше 30с
    const delay = Math.min(
      RECONNECT_BASE_DELAY * 2 ** reconnectAttempts,
      RECONNECT_MAX_DELAY,
    )
    reconnectAttempts += 1

    reconnectTimer = setTimeout(connect, delay)
  }

  function startPing() {
    pingTimer = setInterval(() => {
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }))
      }
    }, PING_INTERVAL)
  }

  function stopPing() {
    if (pingTimer) {
      clearInterval(pingTimer)
      pingTimer = null
    }
  }

  function disconnect() {
    // Убираем обработчик, чтобы закрытие по нашей инициативе
    // не запустило переподключение
    if (socket) {
      socket.onclose = null
      socket.close()
      socket = null
    }
    if (reconnectTimer) clearTimeout(reconnectTimer)
    stopPing()
    isConnected.value = false
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return { isConnected }
}