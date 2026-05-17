<script setup>
import { computed } from 'vue'
import { formatNumber } from '@/utils/format'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], required: true },
  unit: { type: String, default: '' },
  color: { type: String, default: 'var(--color-primary-500)' },
  icon: { type: String, default: '' },
  change: { type: String, default: '' },
  changeType: { type: String, default: 'neutral' },
  clickable: { type: Boolean, default: false },
  delay: { type: Number, default: 0 }
})

const emit = defineEmits(['click'])

const displayValue = computed(() => {
  if (props.value === '-' || props.value === null || props.value === undefined) return '-'
  if (typeof props.value === 'number') return formatNumber(props.value)
  return props.value
})

const iconBgStyle = computed(() => ({
  background: `${props.color}1A`
}))

const iconColorStyle = computed(() => ({
  color: props.color
}))

const topBorderStyle = computed(() => ({
  background: `linear-gradient(90deg, ${props.color}, ${props.color}99)`
}))

const handleClick = () => {
  if (props.clickable) emit('click')
}
</script>

<template>
  <div
    class="stat-card"
    :class="{ 'stat-card-clickable': clickable, 'stat-card-empty': value === '-' }"
    :style="{ '--card-color': color, '--delay': delay + 's' }"
    @click="handleClick"
  >
    <div class="stat-top-border" :style="topBorderStyle"></div>
    <div class="stat-card-inner">
      <div class="stat-icon-wrapper" :style="iconBgStyle">
        <svg
          v-if="icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="stat-icon"
          :style="iconColorStyle"
          v-html="icon"
        />
      </div>
      <div class="stat-content">
        <span class="stat-label">{{ label }}</span>
        <div class="stat-value-row">
          <span class="stat-value">{{ displayValue }}</span>
          <span v-if="unit && value !== '-'" class="stat-unit">{{ unit }}</span>
        </div>
        <div v-if="change && changeType !== 'neutral'" class="stat-change" :class="changeType">
          <svg
            v-if="changeType === 'up'"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="change-icon"
          >
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
            <polyline points="17 6 23 6 23 12" />
          </svg>
          <svg
            v-else-if="changeType === 'down'"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="change-icon"
          >
            <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" />
            <polyline points="17 18 23 18 23 12" />
          </svg>
          <span>{{ change }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-card {
  background: var(--color-neutral-0);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  border: 1px solid var(--color-neutral-200);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.03);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: default;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-3);
  animation: cardSlideIn 0.5s cubic-bezier(0.4, 0, 0.2, 1) backwards;
  animation-delay: var(--delay, 0s);
  min-height: 140px;
}

.stat-card-clickable {
  cursor: pointer;
}

.stat-card-empty {
  opacity: 0.7;
}

.stat-card-empty .stat-value {
  color: var(--color-neutral-400);
}

.stat-card-empty .stat-change {
  visibility: hidden;
}

.stat-top-border {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  opacity: 0.8;
  transition: height 0.3s ease, opacity 0.3s ease;
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: color-mix(in srgb, var(--card-color) 30%, transparent);
}

.stat-card:hover .stat-top-border {
  height: 4px;
}

.stat-card-clickable:active {
  transform: translateY(-1px);
}

.stat-card-inner {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  width: 100%;
}

.stat-icon-wrapper {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-1);
  transition: transform 0.3s ease;
  position: relative;
  overflow: hidden;
  z-index: 1;
}

.stat-card:hover .stat-icon-wrapper {
  transform: scale(1.08);
}

.stat-icon {
  width: 22px;
  height: 22px;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  width: 100%;
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
}

.stat-value-row {
  display: flex;
  align-items: baseline;
  gap: var(--space-1);
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  letter-spacing: var(--tracking-tight);
  line-height: 1.2;
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.stat-unit {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
}

.stat-change {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  margin-top: var(--space-1);
}

.stat-change.up {
  color: var(--color-success-600);
}

.stat-change.down {
  color: var(--color-danger-500);
}

.change-icon {
  width: 14px;
  height: 14px;
}

@keyframes cardSlideIn {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .stat-card {
    animation: none;
  }
}
</style>
