<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  preloadedData: {
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

const fetchBookData = async () => {
  loading.value = true
  try {
    const [statsRes, catRes, hotRes] = await Promise.all([
      fetch('/api/books/stats'),
      fetch('/api/books/categories'),
      fetch('/api/books/hot')
    ])

    if (statsRes.ok) bookStats.value = await statsRes.json()
    if (catRes.ok) categories.value = await catRes.json()
    if (hotRes.ok) {
      const hotData = await hotRes.json()
      console.log('热门图书数据:', hotData)
      hotBooks.value = hotData
    }
  } catch (e) {
    console.error('获取数据失败', e)
  } finally {
    loading.value = false
  }
}

const fetchCategoriesList = async () => {
  try {
    const res = await fetch('/api/books/categories-list')
    if (res.ok) categoriesList.value = await res.json()
  } catch (e) {
    console.error('获取分类列表失败', e)
  }
}

const performSearch = async (page = 1) => {
  searchLoading.value = true
  hasSearched.value = true
  searchPage.value = page
  try {
    const params = new URLSearchParams({
      keyword: searchKeyword.value,
      category: searchCategory.value,
      page: page,
      page_size: searchPageSize.value
    })
    const res = await fetch(`/api/books/search?${params}`)
    if (res.ok) {
      const data = await res.json()
      console.log('检索结果:', data)
      searchResults.value = data.books
      searchTotal.value = data.total
      searchTotalPages.value = data.total_pages
    }
  } catch (e) {
    console.error('检索失败', e)
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

watch(() => props.preloadedData, (data) => {
  if (data && data.stats) {
    bookStats.value = data.stats
    categories.value = data.categories || []
    hotBooks.value = data.hotBooks || []
    loading.value = false
  }
}, { immediate: true })

onMounted(() => {
  if (!props.preloadedData || !props.preloadedData.stats) {
    fetchBookData()
  }
  fetchCategoriesList()
})

const formatNumber = (num) => num.toLocaleString()
</script>

<template>
  <div class="books">
    <div class="page-header">
      <div class="header-content">
        <div>
          <h2>图书管理</h2>
          <p class="page-desc">馆藏图书数据统计</p>
        </div>
        <div class="header-actions">
          <button class="refresh-btn" @click="fetchBookData" :disabled="loading">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ 'spinning': loading }">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            <span>刷新</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>
    </div>
    <template v-else>
      <div class="stats-grid">
        <div class="stat-card" style="--accent: #6366f1">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">总藏书量</span>
            <span class="stat-value">{{ formatNumber(bookStats.total_items) }}</span>
          </div>
          <div class="stat-glow"></div>
        </div>

        <div class="stat-card" style="--accent: #8b5cf6">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">本月入库</span>
            <span class="stat-value">{{ formatNumber(bookStats.month_items) }}</span>
          </div>
          <div class="stat-glow"></div>
        </div>

        <div class="stat-card" style="--accent: #06b6d4">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">借阅率</span>
            <span class="stat-value">{{ bookStats.borrow_rate }}<span class="unit">%</span></span>
          </div>
          <div class="stat-glow"></div>
        </div>

        <div class="stat-card" style="--accent: #ef4444">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </div>
          <div class="stat-info">
            <span class="stat-label">零借阅</span>
            <span class="stat-value">{{ formatNumber(bookStats.zero_borrow) }}</span>
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
            分类占比
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>分类</th>
              <th>数量</th>
              <th>占比</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(cat, index) in categories" :key="cat.name" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td><span class="category-tag">{{ cat.name }}</span></td>
              <td class="count-cell">{{ formatNumber(cat.count) }} <span class="unit">册</span></td>
              <td>
                <div class="percent-bar">
                  <div class="percent-fill" :style="{ width: cat.percent + '%' }"></div>
                  <span class="percent-text">{{ cat.percent }}%</span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card">
        <div class="card-header">
          <h3 class="card-title">
            <span class="title-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
            </span>
            热门图书 TOP 20
          </h3>
        </div>
        <table class="data-table">
          <thead>
            <tr>
              <th>排名</th>
              <th>图书名称</th>
              <th>分类</th>
              <th>借阅次数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(book, index) in hotBooks" :key="book.bib_id" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
              <td>
                <span class="rank-badge" :class="'rank-' + book.rank">{{ book.rank }}</span>
              </td>
              <td class="name-cell">{{ book.name }}</td>
              <td><span class="category-tag">{{ book.category }}</span></td>
              <td class="count-cell">{{ formatNumber(book.borrow_count) }} <span class="unit">次</span></td>
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
            图书检索
          </h3>
        </div>

        <div class="search-form">
          <div class="search-inputs">
            <div class="input-group">
              <label>关键词</label>
              <input 
                v-model="searchKeyword" 
                type="text" 
                placeholder="输入图书名称或关键词"
                @keyup.enter="performSearch(1)"
              />
            </div>
            <div class="input-group">
              <label>分类</label>
              <select v-model="searchCategory">
                <option value="">全部分类</option>
                <option v-for="cat in categoriesList" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
          </div>
          <div class="search-actions">
            <button class="search-btn" @click="performSearch(1)" :disabled="searchLoading">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8"/>
                <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              <span>{{ searchLoading ? '检索中...' : '检索' }}</span>
            </button>
            <button class="reset-btn" @click="resetSearch">重置</button>
          </div>
        </div>

        <div v-if="hasSearched" class="search-results">
          <div class="results-header">
            <span class="results-count">共找到 {{ searchTotal }} 条结果</span>
          </div>

          <div v-if="searchResults.length === 0" class="no-results">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
              <line x1="8" y1="8" x2="14" y2="14"/>
              <line x1="14" y1="8" x2="8" y2="14"/>
            </svg>
            <p>未找到匹配的图书</p>
            <span>请尝试其他关键词或分类</span>
          </div>

          <table v-else class="data-table">
            <thead>
              <tr>
                <th>图书 ID</th>
                <th>图书名称</th>
                <th>分类</th>
                <th>借阅次数</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(book, index) in searchResults" :key="book.bib_id" :style="{ '--delay': index * 0.03 + 's' }" class="table-row">
                <td class="id-cell">#{{ book.bib_id }}</td>
                <td class="name-cell">{{ book.name }}</td>
                <td><span class="category-tag">{{ book.category }}</span></td>
                <td class="count-cell">{{ formatNumber(book.borrow_count) }} <span class="unit">次</span></td>
              </tr>
            </tbody>
          </table>

          <div v-if="searchTotalPages > 1" class="pagination">
            <button 
              class="page-btn" 
              :disabled="searchPage === 1" 
              @click="goToPage(searchPage - 1)"
            >
              上一页
            </button>
            <span class="page-info">第 {{ searchPage }} / {{ searchTotalPages }} 页</span>
            <button 
              class="page-btn" 
              :disabled="searchPage === searchTotalPages" 
              @click="goToPage(searchPage + 1)"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.books {
  max-width: 1280px;
}

.page-header {
  margin-bottom: 28px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 6px 0;
  letter-spacing: -0.02em;
}

.page-desc {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  color: #475569;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.refresh-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #1e293b;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn svg {
  width: 16px;
  height: 16px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 80px;
}

.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #94a3b8;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 22px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(226, 232, 240, 0.6);
  position: relative;
  overflow: hidden;
  transition: all 0.25s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06), 0 8px 24px rgba(0, 0, 0, 0.04);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--accent);
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  z-index: 1;
}

.stat-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.stat-value .unit {
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
}

.stat-glow {
  position: absolute;
  top: -20px;
  right: -20px;
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, color-mix(in srgb, var(--accent) 8%, transparent) 0%, transparent 70%);
  border-radius: 50%;
}

.card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(226, 232, 240, 0.6);
  margin-bottom: 18px;
}

.card-header {
  margin-bottom: 20px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
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
  padding: 14px 16px;
  font-size: 13px;
  font-weight: 600;
  color: #64748b;
  border-bottom: 2px solid #e2e8f0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  padding: 14px 16px;
  font-size: 14px;
  color: #334155;
  border-bottom: 1px solid #f1f5f9;
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
  font-size: 12px;
  color: #10b981;
  background: #ecfdf5;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 500;
}

.count-cell {
  font-weight: 700;
  color: #6366f1;
}

.count-cell .unit {
  font-weight: 500;
  color: #64748b;
}

.name-cell {
  font-weight: 600;
  color: #0f172a;
}

.id-cell {
  font-weight: 600;
  color: #6366f1;
}

.percent-bar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.percent-fill {
  height: 8px;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 4px;
}

.percent-text {
  font-size: 13px;
  font-weight: 600;
  color: #6366f1;
  min-width: 45px;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.rank-1 {
  background: linear-gradient(135deg, #f59e0b, #f97316);
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.rank-2 {
  background: linear-gradient(135deg, #94a3b8, #64748b);
  box-shadow: 0 2px 8px rgba(148, 163, 184, 0.3);
}

.rank-3 {
  background: linear-gradient(135deg, #d97706, #b45309);
  box-shadow: 0 2px 8px rgba(217, 119, 6, 0.3);
}

.rank-4, .rank-5, .rank-6, .rank-7, .rank-8, .rank-9, .rank-10 {
  background: #f1f5f9;
  color: #64748b;
}

.search-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 20px;
}

.search-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
}

.input-group input,
.input-group select {
  padding: 10px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #0f172a;
  background: #ffffff;
  transition: all 0.2s ease;
}

.input-group input:focus,
.input-group select:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.input-group input::placeholder {
  color: #94a3b8;
}

.search-actions {
  display: flex;
  gap: 12px;
}

.search-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 8px;
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.search-btn svg {
  width: 16px;
  height: 16px;
}

.reset-btn {
  padding: 10px 24px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #475569;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.reset-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.search-results {
  margin-top: 16px;
}

.results-header {
  margin-bottom: 16px;
}

.results-count {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.no-results svg {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-results p {
  font-size: 16px;
  font-weight: 600;
  color: #64748b;
  margin: 0 0 8px 0;
}

.no-results span {
  font-size: 14px;
  color: #94a3b8;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.page-btn {
  padding: 8px 16px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #475569;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #cbd5e1;
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-info {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}
</style>
