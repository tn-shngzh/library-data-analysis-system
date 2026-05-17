<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { get } from '@/api/index'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

const { t } = useI18n()

const props = defineProps({
  allData: {
    type: Object,
    default: null
  }
})

const loading = ref(true)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
const categoryList = ref([])

const issueType = ref('')
const category = ref('')
const sortBy = ref('issue')

const issueTypes = [
  { value: '', label: t('intelligence.allTypes') },
  { value: 'never_borrowed', label: t('intelligence.neverBorrowed') },
  { value: 'low_frequency', label: t('intelligence.lowFrequency') },
  { value: 'idle', label: t('intelligence.idle') }
]

const categories = computed(() => [
  { value: '', label: t('intelligence.allCategories') },
  ...categoryList.value.map(cat => ({ value: cat, label: cat }))
])

const sortOptions = [
  { value: 'issue', label: t('intelligence.sortByIssue') },
  { value: 'count', label: t('intelligence.sortByCount') },
  { value: 'date', label: t('intelligence.sortByDate') }
]

const fetchCategories = async () => {
  try {
    const data = await get('/api/books/categories-list')
    categoryList.value = data || []
  } catch (e) {
    console.error('Failed to fetch categories', e)
    categoryList.value = []
  }
}

const formatDate = (dateStr) => {
  if (!dateStr || dateStr === '未知') return '-'
  if (dateStr.length === 8) {
    return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`
  }
  return dateStr
}

const getIssueTypeStyle = (issueType) => {
  switch (issueType) {
    case 'never_borrowed':
      return { background: '#fef2f2', color: '#ef4444' }
    case 'low_frequency':
      return { background: '#fffbeb', color: '#f59e0b' }
    case 'idle':
      return { background: '#f0fdf4', color: '#10b981' }
    default:
      return { background: '#f1f5f9', color: '#64748b' }
  }
}

const getIssueTypeName = (issueType) => {
  const typeMap = {
    'never_borrowed': t('intelligence.neverBorrowed'),
    'low_frequency': t('intelligence.lowFrequency'),
    'idle': t('intelligence.idle')
  }
  return typeMap[issueType] || issueType
}

const sortedList = computed(() => {
  const data = [...list.value]
  switch (sortBy.value) {
    case 'issue':
      return data
    case 'count':
      return data.sort((a, b) => a.borrow_count - b.borrow_count)
    case 'date':
      return data.sort((a, b) => {
        if (!a.last_borrow_date) return 1
        if (!b.last_borrow_date) return -1
        return b.last_borrow_date.localeCompare(a.last_borrow_date)
      })
    default:
      return data
  }
})

const fetchData = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('never_borrowed', 'true')
    params.append('low_freq_threshold', '5')
    params.append('idle_months', '4')
    params.append('page', page.value.toString())
    params.append('page_size', pageSize.value.toString())
    if (issueType.value) params.append('issue_type', issueType.value)
    if (category.value) params.append('category', category.value)

    const data = await get(`/api/intelligence/collection-optimization?${params.toString()}`)
    list.value = data.list || []
    total.value = data.total || 0
  } catch (e) {
    console.error('Failed to fetch optimization list', e)
    list.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const goToPage = (newPage) => {
  if (newPage >= 1 && newPage <= totalPages.value) {
    page.value = newPage
    fetchData()
  }
}

const resetFilters = () => {
  issueType.value = ''
  category.value = ''
  sortBy.value = 'issue'
  page.value = 1
  fetchData()
}

watch([issueType, category], () => {
  page.value = 1
  fetchData()
})

onMounted(async () => {
  await Promise.all([fetchCategories(), fetchData()])
})
</script>

<template>
  <div class="optimization-list">
    <div class="filter-bar">
      <div class="filter-group">
        <label>{{ t('intelligence.issueType') }}</label>
        <select v-model="issueType">
          <option v-for="type in issueTypes" :key="type.value" :value="type.value">
            {{ type.label }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label>{{ t('intelligence.category') }}</label>
        <select v-model="category">
          <option v-for="cat in categories" :key="cat.value" :value="cat.value">
            {{ cat.label }}
          </option>
        </select>
      </div>

      <div class="filter-group">
        <label>{{ t('intelligence.sortBy') }}</label>
        <select v-model="sortBy">
          <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
            {{ opt.label }}
          </option>
        </select>
      </div>

      <div class="filter-summary">
        <span class="total-count">{{ t('intelligence.total') }}: {{ total }}</span>
        <button class="btn-reset" @click="resetFilters">{{ t('common.reset') || '重置' }}</button>
      </div>
    </div>

    <LoadingSpinner :loading="loading" overlay>
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('intelligence.bookName') }}</th>
            <th>{{ t('intelligence.category') }}</th>
            <th>{{ t('intelligence.issueType') }}</th>
            <th>{{ t('intelligence.lastBorrow') }}</th>
            <th>{{ t('intelligence.borrowCount') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in sortedList" :key="item.bib_id">
            <td class="name-cell">{{ item.name }}</td>
            <td>{{ item.category }}</td>
            <td>
              <span class="issue-tag" :style="getIssueTypeStyle(item.issue_type)">
                {{ getIssueTypeName(item.issue_type) }}
              </span>
            </td>
            <td>{{ formatDate(item.last_borrow_date) }}</td>
            <td>{{ item.borrow_count }}</td>
          </tr>
          <tr v-if="sortedList.length === 0">
            <td colspan="5" class="empty-state">{{ t('common.noData') }}</td>
          </tr>
        </tbody>
      </table>
    </LoadingSpinner>

    <div class="pagination" v-if="totalPages > 1">
      <button
        class="page-btn"
        :disabled="page === 1"
        @click="goToPage(page - 1)"
      >
        {{ t('common.prev') }}
      </button>
      <span class="page-info">
        {{ page }} / {{ totalPages }}
      </span>
      <button
        class="page-btn"
        :disabled="page === totalPages"
        @click="goToPage(page + 1)"
      >
        {{ t('common.next') }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.optimization-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 200px);
  max-height: 600px;
  overflow: hidden;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--color-neutral-50, #f8fafc);
  border-radius: 8px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-group label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-neutral-500, #64748b);
}

.filter-group select {
  padding: 8px 12px;
  border: 1px solid var(--color-neutral-200, #e2e8f0);
  border-radius: 6px;
  font-size: 14px;
  color: var(--color-neutral-900, #0f172a);
  background: white;
  min-width: 140px;
  cursor: pointer;
}

.filter-group select:focus {
  outline: none;
  border-color: var(--color-primary-500, #3b82f6);
  box-shadow: 0 0 0 3px var(--color-primary-50, #eff6ff);
}

.filter-summary {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.total-count {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-neutral-700, #334155);
}

.btn-reset {
  padding: 8px 16px;
  border: 1px solid var(--color-neutral-300, #cbd5e1);
  border-radius: 6px;
  background: white;
  font-size: 14px;
  color: var(--color-neutral-600, #475569);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reset:hover {
  background: var(--color-neutral-100, #f1f5f9);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  flex: 1;
  overflow: auto;
}

.data-table th {
  text-align: left;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-neutral-500, #64748b);
  border-bottom: 2px solid var(--color-neutral-200, #e2e8f0);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-neutral-100, #f1f5f9);
  color: var(--color-neutral-700, #334155);
}

.data-table tbody tr:hover td {
  background: var(--color-neutral-50, #f8fafc);
}

.name-cell {
  font-weight: 600;
  color: var(--color-neutral-900, #0f172a);
}

.issue-tag {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--color-neutral-400, #94a3b8);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--color-neutral-200, #e2e8f0);
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid var(--color-neutral-300, #cbd5e1);
  border-radius: 6px;
  background: white;
  font-size: 14px;
  color: var(--color-neutral-700, #334155);
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: var(--color-neutral-100, #f1f5f9);
  border-color: var(--color-primary-500, #3b82f6);
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: var(--color-neutral-500, #64748b);
  font-weight: 500;
}

@media (max-width: 768px) {
  .filter-bar {
    flex-direction: column;
  }

  .filter-summary {
    margin-left: 0;
    margin-top: 8px;
  }

  .filter-group select {
    min-width: 100%;
  }

  .data-table th,
  .data-table td {
    padding: 8px 12px;
  }
}
</style>