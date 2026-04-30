<script setup>
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { bookApi } from '@/api/books'
import { formatNumber } from '@/utils/format'
import { BOOK_STAT_CARDS } from '@/constants'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import PageHeader from '@/components/PageHeader.vue'
import CategoryList from '@/components/CategoryList.vue'

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

const searchKeyword = ref('')
const searchCategory = ref('')
const categoriesList = ref([])
const searchResults = ref([])
const searchTotal = ref(0)
const searchPage = ref(1)
const searchPageSize = ref(20)
const searchTotalPages = ref(0)
const searchLoading = ref(false)
const hasSearched = ref(false)

const statCards = BOOK_STAT_CARDS

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

const fetchCategoriesList = async () => {
  try {
    const res = await bookApi.getCategoriesList()
    if (res.ok) categoriesList.value = await res.json()
  } catch (e) {
    console.error('Failed to fetch categories', e)
  }
}

const performSearch = async (page = 1) => {
  searchLoading.value = true
  hasSearched.value = true
  searchPage.value = page
  try {
    const res = await bookApi.search(searchKeyword.value, searchCategory.value, page, searchPageSize.value)
    if (res.ok) {
      const data = await res.json()
      searchResults.value = data.books
      searchTotal.value = data.total
      searchTotalPages.value = data.total_pages
    }
  } catch (e) {
    console.error('Search failed', e)
  } finally {
    searchLoading.value = false
  }
}

const resetSearch = () => {
  searchKeyword.value = ''
  searchCategory.value = ''
  searchResults.value = []
  searchTotal.value = 0
  searchPage.value = 1
  searchTotalPages.value = 0
  hasSearched.value = false
}

const goToPage = (page) => {
  if (page >= 1 && page <= searchTotalPages.value) {
    performSearch(page)
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
  fetchCategoriesList()
})
</script>

<template>
  <div class="books">
    <PageHeader :title="t('book.title')" :description="t('book.desc')" :loading="loading" @refresh="fetchBookData" />

    <LoadingSpinner :loading="loading">
      <div class="stats-grid">
        <div v-for="card in statCards" :key="card.key" class="stat-card" :style="{ '--accent': card.accent }">
          <div class="stat-info">
            <span class="stat-label">{{ t(card.i18nKey) }}</span>
            <span class="stat-value">{{ formatNumber(bookStats[card.key]) }}</span>
          </div>
          <div class="stat-glow"></div>
        </div>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </span>
            {{ t('book.categoryRatio') }}
          </h3>
        </div>
        <CategoryList :items="categories" />
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </span>
            {{ t('book.hotBooks') }}
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t('book.rank') }}</th>
              <th>{{ t('book.name') }}</th>
              <th>{{ t('book.category') }}</th>
              <th>{{ t('book.borrowCount') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(book, index) in hotBooks" :key="book.bib_id" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td>
                <span class="rank-badge" :class="'rank-' + book.rank">{{ book.rank }}</span>
              </td>
              <td class="name-cell">{{ book.name }}</td>
              <td><span class="category-tag">{{ book.category }}</span></td>
              <td class="count-cell">{{ formatNumber(book.borrow_count) }} <span class="unit">{{ t('common.times') }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
            </span>
            {{ t('book.search') }}
          </h3>
        </div>

        <div class="search-form">
          <div class="search-inputs">
            <div class="input-group">
              <label>{{ t('book.searchPlaceholder') }}</label>
              <input
                v-model="searchKeyword"
                type="text"
                :placeholder="t('book.searchPlaceholder')"
                @keyup.enter="performSearch(1)"
              />
            </div>
            <div class="input-group">
              <label>{{ t('book.category') }}</label>
              <select v-model="searchCategory">
                <option value="">{{ t('book.allCategories') }}</option>
                <option v-for="cat in categoriesList" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
          </div>
          <div class="search-actions">
            <button class="btn btn-primary search-btn" @click="performSearch(1)" :disabled="searchLoading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <span>{{ searchLoading ? t('common.searching') : t('common.search') }}</span>
            </button>
            <button class="btn btn-secondary reset-btn" @click="resetSearch">{{ t('book.resetBtn') }}</button>
          </div>
        </div>

        <div v-if="hasSearched" class="search-results">
          <div class="results-header">
            <span class="results-count">{{ t('common.total') }} {{ searchTotal }} {{ t('common.found') }}</span>
          </div>

          <div v-if="searchResults.length === 0" class="no-results">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              <line x1="8" y1="8" x2="14" y2="14"/>
              <line x1="14" y1="8" x2="8" y2="14"/>
            </svg>
            <p>{{ t('common.noResults') }}</p>
            <span>{{ t('common.noResultsDesc') }}</span>
          </div>

          <table v-else class="data-table">
            <thead>
              <tr>
                <th>{{ t('borrow.bookId') }}</th>
                <th>{{ t('book.name') }}</th>
                <th>{{ t('book.category') }}</th>
                <th>{{ t('book.borrowCount') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(book, index) in searchResults" :key="book.bib_id" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
                <td class="id-cell">#{{ book.bib_id }}</td>
                <td class="name-cell">{{ book.name }}</td>
                <td><span class="category-tag">{{ book.category }}</span></td>
                <td class="count-cell">{{ formatNumber(book.borrow_count) }} <span class="unit">{{ t('common.times') }}</span></td>
              </tr>
            </tbody>
          </table>

          <div v-if="searchTotalPages > 1" class="pagination">
            <button
              class="btn btn-secondary btn-sm page-btn"
              :disabled="searchPage === 1"
              @click="goToPage(searchPage - 1)"
            >
              {{ t('common.prev') }}
            </button>
            <span class="page-info">{{ t('common.page') }} {{ searchPage }} / {{ searchTotalPages }} {{ t('common.pageOf') }}</span>
            <button
              class="btn btn-secondary btn-sm page-btn"
              :disabled="searchPage === searchTotalPages"
              @click="goToPage(searchPage + 1)"
            >
              {{ t('common.next') }}
            </button>
          </div>
        </div>
      </div>
    </LoadingSpinner>
  </div>
</template>

<style scoped>
.books {
  max-width: var(--main-max-width);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-neutral-0);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  border: 1px solid var(--color-neutral-200);
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
  transition: all var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-neutral-300);
  box-shadow: var(--shadow-lg);
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
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
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
  transition: opacity var(--transition-base);
}

.stat-card:hover .stat-glow {
  opacity: 1.5;
}

.card {
  background: var(--color-neutral-0);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  border: 1px solid var(--color-neutral-200);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-4);
  transition: box-shadow var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-neutral-100);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.title-icon {
  width: 32px;
  height: 32px;
  background: var(--gradient-primary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.title-icon svg {
  width: 16px;
  height: 16px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-500);
  border-bottom: 2px solid var(--color-neutral-200);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.data-table td {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  color: var(--color-neutral-700);
  border-bottom: 1px solid var(--color-neutral-100);
  transition: background var(--transition-fast);
}

.data-table tbody tr:hover td {
  background: var(--color-neutral-50);
}

.table-row {
  animation: fadeIn 0.3s ease backwards;
  animation-delay: var(--delay);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.category-tag {
  font-size: var(--text-xs);
  color: var(--color-success-600);
  background: var(--color-success-50);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-weight: var(--font-medium);
  white-space: nowrap;
}

.count-cell {
  font-weight: var(--font-semibold);
  color: var(--color-primary-600);
}

.count-cell .unit {
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
}

.name-cell {
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.id-cell {
  font-weight: var(--font-semibold);
  color: var(--color-primary-600);
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  color: #fff;
  transition: transform var(--transition-fast);
}

.rank-badge:hover {
  transform: scale(1.1);
}

.rank-1 {
  background: var(--gradient-warm);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.rank-2 {
  background: linear-gradient(135deg, var(--color-neutral-400), var(--color-neutral-500));
  box-shadow: 0 2px 8px rgba(148, 163, 184, 0.3);
}

.rank-3 {
  background: linear-gradient(135deg, var(--color-warning-600), #92400e);
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.3);
}

.rank-4, .rank-5, .rank-6, .rank-7, .rank-8, .rank-9, .rank-10 {
  background: var(--color-neutral-100);
  color: var(--color-neutral-500);
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--color-neutral-50);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-5);
  border: 1px solid var(--color-neutral-100);
}

.search-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.input-group label {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-600);
}

.input-group input,
.input-group select {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-neutral-900);
  background: var(--color-neutral-0);
  transition: all var(--transition-base);
  font-family: var(--font-sans);
}

.input-group input:focus,
.input-group select:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px var(--color-primary-50);
}

.input-group input::placeholder {
  color: var(--color-neutral-400);
}

.search-actions {
  display: flex;
  gap: var(--space-3);
}

.search-btn:disabled {
  box-shadow: none;
}

.search-btn svg {
  width: 16px;
  height: 16px;
}

.search-results {
  margin-top: var(--space-4);
}

.results-header {
  margin-bottom: var(--space-4);
}

.results-count {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-5);
  color: var(--color-neutral-400);
}

.no-results svg {
  width: 64px;
  height: 64px;
  margin-bottom: var(--space-4);
  opacity: 0.5;
}

.no-results p {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-500);
  margin: 0 0 var(--space-2) 0;
}

.no-results span {
  font-size: var(--text-sm);
  color: var(--color-neutral-400);
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-neutral-200);
}

.page-info {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-3);
  }

  .card {
    padding: var(--space-4);
  }

  .search-inputs {
    grid-template-columns: 1fr;
  }

  .data-table th,
  .data-table td {
    padding: var(--space-2) var(--space-3);
    font-size: var(--text-xs);
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .search-actions {
    flex-direction: column;
  }

  .search-btn,
  .reset-btn {
    width: 100%;
  }

  .pagination {
    flex-wrap: wrap;
  }
}
</style>
