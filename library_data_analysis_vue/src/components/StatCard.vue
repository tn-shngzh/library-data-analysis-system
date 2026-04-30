<script setup>
import { formatNumber } from '@/utils/format'

defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], required: true },
  unit: { type: String, default: '' },
  accent: { type: String, default: '#d97706' }
})
</script>

<template>
  <div class="stat-card" :style="{ '--accent': accent }">
    <div class="stat-info">
      <span class="stat-label">{{ label }}</span>
      <span class="stat-value">{{ formatNumber(value) }}<span v-if="unit" class="unit"> {{ unit }}</span></span>
    </div>
    <div class="stat-glow"></div>
  </div>
</template>

<style scoped>
.stat-card {
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  border: 1px solid var(--color-neutral-200);
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
  transition: all var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-neutral-300);
  box-shadow: var(--shadow-md);
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: relative;
  z-index: 1;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  letter-spacing: var(--tracking-tight);
}

.stat-value .unit {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
}

.stat-glow {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 10%, transparent) 0%, transparent 70%);
  border-radius: 50%;
}
</style>