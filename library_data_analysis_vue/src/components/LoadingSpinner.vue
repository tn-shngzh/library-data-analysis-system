<script setup>
defineProps({
  loading: { type: Boolean, default: true },
  text: { type: String, default: '加载中...' }
})
</script>

<template>
  <div v-if="loading" class="loading-container">
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