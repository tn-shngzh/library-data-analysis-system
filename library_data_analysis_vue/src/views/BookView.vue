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

const bookStats = ref({
  total_items: 0,
  month_items: 0,
  borrow_rate: 0,
  zero_borrow: 0
})

const categories = ref([])
const hotBooks = ref([])
const loading = ref(true)



const bookColor = 'var(--data-book)'

const formatNumber = (num) => {
  if (!num && num !== 0) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const categoryStats = computed(() => [
  { label: t('book.totalItems'), value: formatNumber(bookStats.value.total_items) },
  { label: t('book.borrowRate'), value: bookStats.value.borrow_rate + '%' }
])

const hotBookStats = computed(() => [
  { label: t('book.monthItems'), value: formatNumber(bookStats.value.month_items) },
  { label: t('book.zeroBorrow'), value: formatNumber(bookStats.value.zero_borrow) }
])

const categoryPieOption = computed(() => {
  if (!categories.value.length) return {}
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { type: 'scroll', bottom: 0, left: 'center', textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '45%'],
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { show: true, formatter: '{b}\n{d}%', fontSize: 11 },
      emphasis: { label: { show: true, fontSize: 12, fontWeight: 'bold' } },
      data: categories.value.map(c => ({ name: c.name, value: c.count }))
    }]
  }
})

const hotBookBarOption = computed(() => {
  if (!hotBooks.value.length) return {}
  const data = hotBooks.value.slice(0, 10)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '8%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', name: t('book.borrowCount') },
    yAxis: {
      type: 'category',
      data: data.map(b => b.name || String(b.bib_id)).reverse(),
      axisLabel: { fontSize: 11 }
    },
    series: [{
      type: 'bar',
      data: data.map(b => b.borrow_count).reverse(),
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#6366f1' },
      barWidth: '60%'
    }]
  }
})

const fetchBookData = async () => {
  loading.value = true
  try {
    const data = await bookApi.getAll()
    if (data.stats) bookStats.value = data.stats
    if (data.categories) categories.value = data.categories
    if (data.hotBooks) hotBooks.value = data.hotBooks
  } catch (e) {
    console.error('Failed to fetch book data', e)
  } finally {
    loading.value = false
  }
}

watch(() => props.allData?.books, (data) => {
  if (data && data.stats) {
    bookStats.value = data.stats
    categories.value = data.categories || []
    hotBooks.value = data.hotBooks || []
    loading.value = false
  }
}, { immediate: true })

onMounted(() => {
  if (!props.allData?.books || !props.allData.books.stats) {
    fetchBookData()
  }
})
</script>

<template>
  <div class="books">
    <PageHeader :title="t('book.title')" :description="t('book.desc')" :loading="loading" @refresh="fetchBookData" />

    <LoadingSpinner :loading="loading">
      <div class="charts-row">
        <ChartCard :title="t('book.categoryRatio')" :color="bookColor" :stats="categoryStats" icon="<path d='M22 12h-4l-3 9L9 3l-3 9H2'/>">
          <div class="chart-container">
            <v-chart class="chart" :option="categoryPieOption" autoresize />
          </div>
        </ChartCard>

        <ChartCard :title="t('book.hotBooks')" :color="bookColor" :stats="hotBookStats" icon="<polygon points='12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2'/>">
          <div class="chart-container">
            <v-chart class="chart" :option="hotBookBarOption" autoresize />
          </div>
        </ChartCard>
      </div>

    </LoadingSpinner>
  </div>
</template>

<style scoped>
.books {
  max-width: var(--main-max-width);
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--header-height) - 48px);
  overflow: hidden;
  gap: var(--space-3);
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
  flex: 1;
  min-height: 0;
}

.charts-row :deep(.chart-card) {
  height: 100%;
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

@media (max-width: 1024px) {
  .charts-row {
    grid-template-columns: 1fr;
  }
}
</style>
