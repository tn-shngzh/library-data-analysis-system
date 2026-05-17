<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { bookApi } from '@/api/books'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'
import ChartCard from '@/components/ChartCard.vue'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const loading = ref(true)
const activeTab = ref('category')
const categories = ref([])
const borrowByCategory = ref([])
const categoryTrend = ref([])

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const totalBooks = computed(() => categories.value.reduce((s, c) => s + (c.count || 0), 0))
const totalBorrows = computed(() => borrowByCategory.value.reduce((s, c) => s + (c.count || 0), 0))
const avgBorrowRate = computed(() => {
  if (totalBooks.value === 0) return '0%'
  return (totalBorrows.value / totalBooks.value * 100).toFixed(1) + '%'
})

const topCategory = computed(() => {
  if (!categories.value.length) return '-'
  return categories.value[0]?.name || '-'
})

const categoryColor = 'var(--data-category)'

const chartStats = computed(() => [
  { label: t('category.categoryCount'), value: String(categories.value.length) },
  { label: t('category.totalBooks'), value: formatNumber(totalBooks.value) },
  { label: t('category.totalBorrows'), value: formatNumber(totalBorrows.value) },
  { label: t('category.topCategory'), value: topCategory.value }
])

const categoryBarOption = computed(() => {
  if (!categories.value.length) return {}
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '10%', top: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      data: categories.value.map(c => c.name),
      axisLabel: { rotate: 30, fontSize: 11 }
    },
    yAxis: { type: 'value', name: t('category.count') },
    series: [{
      type: 'bar',
      data: categories.value.map(c => c.count),
      itemStyle: { borderRadius: [4, 4, 0, 0], color: '#6366f1' },
      barWidth: '50%'
    }]
  }
})

const borrowBarOption = computed(() => {
  if (!borrowByCategory.value.length) return {}
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '10%', top: '5%', containLabel: true },
    xAxis: {
      type: 'category',
      data: borrowByCategory.value.map(c => c.name),
      axisLabel: { rotate: 30, fontSize: 11 }
    },
    yAxis: { type: 'value', name: t('category.count') },
    series: [{
      type: 'bar',
      data: borrowByCategory.value.map(c => c.count),
      itemStyle: { borderRadius: [4, 4, 0, 0], color: '#f59e0b' },
      barWidth: '50%'
    }]
  }
})

const fetchCategoryData = async () => {
  loading.value = true
  try {
    const bookData = await bookApi.getAll()
    if (bookData.categories) {
      categories.value = bookData.categories
      borrowByCategory.value = bookData.categories
    }
  } catch (e) {
    console.error('Failed to fetch category data', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.allData, (data) => {
  if (data) {
    if (data.books?.categories) {
      categories.value = data.books.categories
      borrowByCategory.value = data.books.categories
    }
    if (data.overview?.categories) {
      if (!categories.value.length) categories.value = data.overview.categories
    }
    loading.value = false
  }
}, { immediate: true, deep: true })

onMounted(() => {
  if (!props.allData || !props.allData.books?.categories) {
    fetchCategoryData()
  }
})
</script>

<template>
  <div class="category-view">
    <PageHeader :title="t('category.title')" :description="t('category.desc')" :loading="loading" @refresh="fetchCategoryData" />

    <LoadingSpinner :loading="loading">
      <div class="tab-bar">
        <button class="tab-btn btn-tab" :class="{ active: activeTab === 'category' }" @click="activeTab = 'category'">{{ t('category.categoryRatio') }}</button>
        <button class="tab-btn btn-tab" :class="{ active: activeTab === 'borrow' }" @click="activeTab = 'borrow'">{{ t('category.borrowAnalysis') }}</button>
      </div>

      <ChartCard :title="activeTab === 'category' ? t('category.categoryRatio') : t('category.borrowAnalysis')" :color="categoryColor" :stats="chartStats">
        <div class="chart-container">
          <v-chart v-if="activeTab === 'category'" class="chart" :option="categoryBarOption" autoresize />
          <v-chart v-else class="chart" :option="borrowBarOption" autoresize />
        </div>
      </ChartCard>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.category-view {
  max-width: var(--main-max-width);
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - 48px);
  overflow: hidden;
  gap: var(--space-3);
}

.tab-bar {
  display: flex;
  gap: 4px;
  background: var(--color-neutral-100);
  padding: 4px;
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}

.tab-btn {
  flex: 1;
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  color: var(--color-neutral-500);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--color-neutral-700);
}

.tab-btn.active {
  background: var(--color-neutral-0);
  color: var(--color-primary-600);
  box-shadow: var(--shadow-sm);
}

.chart-container {
  width: 100%;
  height: 100%;
  flex: 1;
  min-height: 0;
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 280px;
}
</style>
