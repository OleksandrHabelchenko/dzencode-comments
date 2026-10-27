<script setup>
// Анимированный фон на Vanta.js (эффект cells).
//
// Эффект рендерится на WebGL, поэтому создаётся после появления
// компонента в DOM и обязательно уничтожается при удалении —
// иначе остаётся работать в фоне и ест ресурсы.

import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import CellsModule from 'vanta/dist/vanta.cells.min'

// Vanta собран как UMD-модуль: функция лежит в default,
// но при некоторых сборках приходит сам объект — берём то, что есть
const CELLS = CellsModule.default || CellsModule

const container = ref(null)
let vantaEffect = null

onMounted(() => {
  vantaEffect = CELLS({
    el: container.value,
    THREE,

    // Управление мышью отключено: фон не должен реагировать
    // на движения курсора, когда пользователь читает комментарии
    mouseControls: false,
    touchControls: false,
    gyroControls: false,

    minHeight: 200,
    minWidth: 200,
    scale: 1,

    // Цвета приглушены относительно демо: яркий синий
    // забивал бы текст поверх него
    color1: 0x1a2740,
    color2: 0x2d4a7c,

    size: 2.6,
    // Скорость снижена: медленное движение не отвлекает
    speed: 0.5,
  })
})

onUnmounted(() => {
  // destroy() освобождает контекст WebGL
  vantaEffect?.destroy()
})
</script>

<template>
  <div class="vanta" aria-hidden="true">
    <div ref="container" class="vanta__canvas" />
    <!-- Затемняющий слой поверх эффекта: сохраняет контраст
         текста, не убирая движение фона -->
    <div class="vanta__overlay" />
  </div>
</template>

<style scoped>
.vanta {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}

.vanta__canvas {
  width: 100%;
  height: 100%;
}

.vanta__overlay {
  position: absolute;
  inset: 0;
  background: rgba(8, 10, 15, 0.55);
}
</style>
