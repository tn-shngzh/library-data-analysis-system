<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  showRefresh: { type: Boolean, default: true },
  loading: { type: Boolean, default: false }
})

defineEmits(['refresh'])
</script>

<template>
  <div class="page-header">
    <div class="header-content">
      <div>
        <h2>{{ title }}</h2>
        <p v-if="description" class="page-desc">{{ description }}</p>
      </div>
      <div v-if="showRefresh" class="header-actions">
        <button class="refresh-btn btn btn-secondary btn-sm" @click="$emit('refresh')" :disabled="loading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'spinning': loading }">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
          <span>刷新</span>
        </button>
        <slot name="actions" />
      </div>
      <slot v-else name="actions" />
    </div>
  </div>
</template>

<style scoped>
.page-header {
  margin-bottom: var(--space-7);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  margin: 0 0 var(--space-1) 0;
  letter-spacing: var(--tracking-tight);
}

.page-desc {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.refresh-btn svg {
  width: 16px;
  height: 16px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>