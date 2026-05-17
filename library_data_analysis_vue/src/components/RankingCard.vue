<script setup>
const props = defineProps({
  items: { type: Array, default: () => [] },
  color: { type: String, default: '#1677ff' }
})

const formatNumber = (n) => {
  if (!n && n !== 0) return '0'
  return n.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const getBadgeClass = (rank) => {
  if (rank === 1) return 'badge-gold'
  if (rank === 2) return 'badge-silver'
  if (rank === 3) return 'badge-bronze'
  return 'badge-default'
}
</script>

<template>
  <div class="ranking-card">
    <div v-if="items.length === 0" class="ranking-empty">暂无数据</div>
    <div v-else class="ranking-list">
      <div 
        v-for="(item, idx) in items.slice(0, 8)" 
        :key="item.rank || idx"
        class="ranking-item"
      >
        <div class="ranking-left">
          <span class="ranking-badge" :class="getBadgeClass(item.rank)">
            {{ item.rank }}
          </span>
          <div class="ranking-info">
            <span class="ranking-name">{{ item.name || item.title || item.bib_id || '未知' }}</span>
            <span class="ranking-meta">{{ item.meta || item.category || '' }}</span>
          </div>
        </div>
        <div class="ranking-right">
          <span class="ranking-value" :style="{ color }">{{ formatNumber(item.value || item.borrow_count || item.borrowed || 0) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ranking-card {
  padding: 8px 0;
}

.ranking-empty {
  text-align: center;
  color: #9ca3af;
  padding: 40px 0;
  font-size: 14px;
}

.ranking-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ranking-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 8px;
  transition: background 0.2s;
}

.ranking-item:hover {
  background: #f3f4f6;
}

.ranking-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.ranking-badge {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.badge-gold { background: linear-gradient(135deg, #f59e0b, #d97706); }
.badge-silver { background: linear-gradient(135deg, #6b7280, #4b5563); }
.badge-bronze { background: linear-gradient(135deg, #92400e, #78350f); }
.badge-default { background: #e5e7eb; color: #6b7280; }

.ranking-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.ranking-name {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.ranking-meta {
  font-size: 11px;
  color: #9ca3af;
}

.ranking-right {
  flex-shrink: 0;
}

.ranking-value {
  font-size: 14px;
  font-weight: 700;
}
</style>
