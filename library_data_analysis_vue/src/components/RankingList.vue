<script setup>
import { computed } from 'vue'
import { formatNumber } from '@/utils/format'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  color: {
    type: String,
    default: 'var(--color-primary-500)'
  },
  maxValue: {
    type: Number,
    default: 0
  },
  delay: {
    type: Number,
    default: 0
  }
})

const safeMax = computed(() => {
  if (props.maxValue > 0) return props.maxValue
  const max = Math.max(...props.items.map(i => i.value || 0), 0)
  return max > 0 ? max : 1
})

const getRankClass = (rank) => {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return 'rank-normal'
}

const getBarWidth = (value) => {
  return Math.min((value / safeMax.value) * 100, 100)
}
</script>

<template>
  <div class="ranking-list" :style="{ '--rank-color': color, '--delay': delay + 's' }">
    <div
      v-for="(item, index) in items"
      :key="item.rank || index"
      class="ranking-item"
      :style="{ animationDelay: (delay + index * 0.03) + 's' }"
    >
      <div class="rank-badge" :class="getRankClass(item.rank)">
        {{ item.rank }}
      </div>
      <div class="rank-info">
        <span class="rank-name">{{ item.name }}</span>
        <span v-if="item.meta" class="rank-meta">{{ item.meta }}</span>
      </div>
      <div class="rank-bar">
        <div
          class="rank-bar-fill"
          :style="{ width: getBarWidth(item.value) + '%', background: color }"
        ></div>
      </div>
      <span class="rank-value">{{ formatNumber(item.value) }}</span>
    </div>
    <div v-if="!items.length" class="ranking-empty">
      <span>暂无数据</span>
    </div>
  </div>
</template>

<style scoped>
.ranking-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  animation: contentFadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) backwards;
  animation-delay: var(--delay, 0s);
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
  transition: background var(--transition-base);
  animation: rankItemIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) backwards;
}

.ranking-item:hover {
  background: var(--color-neutral-100);
}

.rank-badge {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  color: white;
  flex-shrink: 0;
}

.rank-gold {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.rank-silver {
  background: linear-gradient(135deg, #94a3b8, #64748b);
  box-shadow: 0 2px 8px rgba(148, 163, 184, 0.3);
}

.rank-bronze {
  background: linear-gradient(135deg, #b45309, #92400e);
  box-shadow: 0 2px 8px rgba(180, 83, 9, 0.3);
}

.rank-normal {
  background: var(--color-neutral-200);
  color: var(--color-neutral-600);
}

.rank-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.rank-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rank-meta {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}

.rank-bar {
  width: 60px;
  height: 6px;
  background: var(--color-neutral-100);
  border-radius: 3px;
  overflow: hidden;
  flex-shrink: 0;
}

.rank-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.rank-value {
  font-size: var(--text-sm);
  font-weight: var(--font-bold);
  color: var(--rank-color);
  min-width: 40px;
  text-align: right;
  flex-shrink: 0;
}

.ranking-empty {
  padding: var(--space-8);
  text-align: center;
  color: var(--color-neutral-400);
  font-size: var(--text-sm);
}

@keyframes rankItemIn {
  from {
    opacity: 0;
    transform: translateX(-8px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes contentFadeIn {
  from { opacity: 0.3; }
  to { opacity: 1; }
}

@media (prefers-reduced-motion: reduce) {
  .ranking-list,
  .ranking-item {
    animation: none;
  }
}
</style>
