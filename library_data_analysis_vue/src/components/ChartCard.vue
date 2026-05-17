<script setup>
defineProps({
  title: { type: String, required: true },
  icon: { type: String, default: '' },
  color: { type: String, default: 'var(--color-primary-500)' },
  loading: { type: Boolean, default: false },
  delay: { type: Number, default: 0 },
  stats: { type: Array, default: () => [] }
})
</script>

<template>
  <div
    class="chart-card"
    :style="{ '--card-color': color, '--delay': delay + 's' }"
  >
    <div class="chart-card-header">
      <div class="chart-title-bar" :style="{ background: color }"></div>
      <h3 class="chart-title">
        <svg
          v-if="icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          class="chart-title-icon"
          v-html="icon"
        />
        {{ title }}
      </h3>
      <div v-if="stats.length" class="chart-card-stats">
        <div v-for="s in stats" :key="s.label" class="chart-stat">
          <span class="chart-stat-label">{{ s.label }}</span>
          <span class="chart-stat-value">{{ s.value }}</span>
        </div>
      </div>
      <div v-if="$slots.actions" class="chart-card-actions">
        <slot name="actions" />
      </div>
    </div>
    <div v-if="loading" class="chart-loading-state">
      <div class="chart-skeleton skeleton-pulse"></div>
    </div>
    <div v-else class="chart-card-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.chart-card {
  background: var(--chart-bg);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  border: 1px solid var(--color-neutral-200);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.03);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: chartFadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1) backwards;
  animation-delay: var(--delay, 0s);
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chart-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04);
}

.chart-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-neutral-100);
  flex-shrink: 0;
}

.chart-title-bar {
  width: 3px;
  height: 16px;
  border-radius: 2px;
  flex-shrink: 0;
}

.chart-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  margin: 0;
  flex-shrink: 0;
}

.chart-title-icon {
  width: 18px;
  height: 18px;
  color: var(--card-color);
}

.chart-card-stats {
  display: flex;
  gap: var(--space-4);
  flex: 1;
  justify-content: flex-end;
  min-width: 0;
}

.chart-stat {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 1px;
}

.chart-stat-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
  white-space: nowrap;
}

.chart-stat-value {
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  white-space: nowrap;
}

.chart-card-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.chart-card-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.chart-loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  animation: contentFadeIn 0.3s ease;
}

.chart-skeleton {
  width: 100%;
  height: 200px;
  border-radius: var(--radius-lg);
}

.skeleton-pulse {
  background: linear-gradient(90deg, var(--color-neutral-100) 25%, var(--color-neutral-50) 50%, var(--color-neutral-100) 75%);
  background-size: 200% 100%;
  animation: skeletonPulse 1.5s ease-in-out infinite;
}

@keyframes chartFadeIn {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes contentFadeIn {
  from { opacity: 0.3; }
  to { opacity: 1; }
}

@keyframes skeletonPulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

@media (prefers-reduced-motion: reduce) {
  .chart-card {
    animation: none;
  }
}
</style>
