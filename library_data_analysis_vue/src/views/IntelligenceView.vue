<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import CorrelationChart from './CorrelationChart.vue'
import OptimizationList from './OptimizationList.vue'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const activeTab = ref('correlation')

const tabs = [
  { id: 'correlation', label: t('intelligence.correlation') },
  { id: 'optimization', label: t('intelligence.optimization') }
]

const setActiveTab = (tabId) => {
  activeTab.value = tabId
}
</script>

<template>
  <div class="intelligence-view">
    <div class="page-header">
      <h1>{{ t('intelligence.title') }}</h1>
      <p>{{ t('intelligence.desc') }}</p>
    </div>

    <div class="tabs-container">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-btn"
        :class="{ active: activeTab === tab.id }"
        @click="setActiveTab(tab.id)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="tab-content">
      <CorrelationChart v-if="activeTab === 'correlation'" :all-data="allData" />
      <OptimizationList v-if="activeTab === 'optimization'" :all-data="allData" />
    </div>
  </div>
</template>

<style scoped>
.intelligence-view {
  max-width: var(--main-max-width);
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - 48px);
  overflow: hidden;
  gap: var(--space-3);
}

.page-header {
  flex-shrink: 0;
}

.page-header h1 {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  margin: 0 0 var(--space-1) 0;
}

.page-header p {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin: 0;
}

.tabs-container {
  display: flex;
  gap: var(--space-2);
  flex-shrink: 0;
}

.tab-btn {
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
  transition: all 0.2s;
}

.tab-btn:hover:not(.active) {
  background: var(--color-neutral-100);
}

.tab-btn.active {
  background: var(--color-primary-500);
  color: #fff;
}

.tab-content {
  background: var(--chart-bg);
  border-radius: var(--radius-xl);
  padding: var(--space-4) var(--space-5);
  border: 1px solid var(--color-neutral-200);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.03);
  flex: 1;
  min-height: 0;
  overflow: auto;
}
</style>