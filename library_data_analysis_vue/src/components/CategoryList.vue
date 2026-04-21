<script setup>
defineProps({
  items: { type: Array, required: true },
  valueKey: { type: String, default: 'count' },
  nameKey: { type: String, default: 'name' },
  unit: { type: String, default: '册' }
})

import { formatNumber } from '@/utils/format'
</script>

<template>
  <div class="category-list">
    <div v-for="(item, index) in items" :key="item[nameKey]" class="category-item" :style="{ '--delay': `${index * 0.05}s` }">
      <div class="category-info">
        <span class="category-name">{{ item[nameKey] }}</span>
        <span class="category-count">{{ formatNumber(item[valueKey]) }} <span class="unit">{{ unit }}</span></span>
      </div>
      <div class="category-bar">
        <div class="category-fill" :style="{ width: `${items[0] ? (item[valueKey] / items[0][valueKey]) * 100 : 0}%` }"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  animation: slideInLeft 0.3s ease backwards;
  animation-delay: var(--delay);
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.category-name {
  font-size: var(--text-sm);
  color: var(--color-neutral-700);
  font-weight: var(--font-medium);
}

.category-count {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  font-weight: var(--font-semibold);
}

.category-count .unit {
  font-weight: var(--font-regular);
  color: var(--color-neutral-500);
}

.category-bar {
  height: 6px;
  background: var(--color-neutral-100);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.category-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-12px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>