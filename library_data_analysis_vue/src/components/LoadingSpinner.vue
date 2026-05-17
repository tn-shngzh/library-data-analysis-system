<script setup>
defineProps({
  loading: { type: Boolean, default: true },
  text: { type: String, default: '加载中...' },
  overlay: { type: Boolean, default: false }
})
</script>

<template>
  <div v-if="loading" class="loading-container" :class="{ 'overlay-mode': overlay }">
    <div class="loading-spinner">
      <div class="spinner"></div>
      <span>{{ text }}</span>
    </div>
  </div>
  <slot v-else />
</template>

<style scoped>
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px;
}

.loading-container.overlay-mode {
  position: relative;
  min-height: 200px;
}

.loading-container.overlay-mode::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 8px;
  z-index: 1;
}

.loading-container.overlay-mode .loading-spinner {
  position: relative;
  z-index: 2;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  color: var(--color-neutral-500);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-neutral-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>