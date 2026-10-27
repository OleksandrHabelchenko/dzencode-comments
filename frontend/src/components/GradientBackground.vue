<script setup>
// Градиентный фон Horizon: #003973 -> #e5e5be.
//
// Чистый CSS без библиотек и без затемняющих слоёв —
// цвета ровно те, что выбраны в палитре.
</script>

<template>
  <div class="gradient" aria-hidden="true" />
</template>

<style scoped>
.gradient {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background: linear-gradient(135deg, #003973 0%, #e5e5be 100%);
}
</style>
