<script setup>
import { ref, onMounted, reactive } from 'vue'
import OverviewView from './OverviewView.vue'
import { overviewApi } from '@/api/overview'
import { readerApi } from '@/api/readers'
import { bookApi } from '@/api/books'
import { borrowApi } from '@/api/borrows'
import { useAuth } from '@/composables/useAuth'
import { useTime } from '@/composables/useTime'

const { username, role, checkAuth, logout } = useAuth()
const { currentTime } = useTime()

const dataLoaded = ref(false)
const sidebarCollapsed = ref(false)

const allData = reactive({
  overview: { stats: null, categories: null, recentBooks: null },
  readers: { stats: null, readerTypes: null, monthlyTrend: null, topReaders: null },
  books: { stats: null, categories: null, hotBooks: null },
  borrows: { stats: null, actionStats: null, degreeStats: null, topBorrowers: null, topBooks: null, recentBorrows: null }
})

const preloadData = async () => {
  try {
    const [overviewResult, readerResult, bookResult, borrowResult] = await Promise.all([
      overviewApi.getAll(),
      readerApi.getAll(),
      bookApi.getAll(),
      borrowApi.getAll()
    ])

    if (overviewResult.stats) allData.overview.stats = overviewResult.stats
    if (overviewResult.categories) allData.overview.categories = overviewResult.categories
    if (overviewResult.recentBooks) allData.overview.recentBooks = overviewResult.recentBooks

    if (readerResult.stats) allData.readers.stats = readerResult.stats
    if (readerResult.readerTypes) allData.readers.readerTypes = readerResult.readerTypes
    if (readerResult.monthlyTrend) allData.readers.monthlyTrend = readerResult.monthlyTrend
    if (readerResult.topReaders) allData.readers.topReaders = readerResult.topReaders

    if (bookResult.stats) allData.books.stats = bookResult.stats
    if (bookResult.categories) allData.books.categories = bookResult.categories
    if (bookResult.hotBooks) allData.books.hotBooks = bookResult.hotBooks

    if (borrowResult.stats) allData.borrows.stats = borrowResult.stats
    if (borrowResult.actionStats) allData.borrows.actionStats = borrowResult.actionStats
    if (borrowResult.degreeStats) allData.borrows.degreeStats = borrowResult.degreeStats
    if (borrowResult.topBorrowers) allData.borrows.topBorrowers = borrowResult.topBorrowers
    if (borrowResult.topBooks) allData.borrows.topBooks = borrowResult.topBooks
    if (borrowResult.recentBorrows) allData.borrows.recentBorrows = borrowResult.recentBorrows

    dataLoaded.value = true
  } catch (e) {
    console.error('预加载数据失败', e)
    dataLoaded.value = true
  }
}

onMounted(async () => {
  if (!checkAuth()) return
  await preloadData()
})

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="dashboard">
    <header class="header">
      <div class="header-left">
        <button class="sidebar-toggle" @click="toggleSidebar" :class="{ collapsed: sidebarCollapsed }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>
        <div class="logo-wrapper">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <div class="title-group">
            <h1>图书数据分析系统</h1>
            <span class="subtitle">LIBRARY DATA ANALYTICS</span>
          </div>
        </div>
      </div>

      <div class="header-center">
        <div class="page-tabs">
          <button class="tab active">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="tab-icon">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
            </svg>
            数据总览
          </button>
          <span class="tab-desc">实时监控图书流通数据，洞察数据价值</span>
        </div>
      </div>
      
      <div class="header-right">
        <div class="datetime-picker">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="calendar-icon">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <span class="date-text">{{ currentTime }}</span>
        </div>

        <div class="header-actions">
          <button class="icon-btn" title="全屏">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 3 21 3 21 9"/>
              <polyline points="9 21 3 21 3 15"/>
              <line x1="21" y1="3" x2="14" y2="10"/>
              <line x1="3" y1="21" x2="10" y2="14"/>
            </svg>
          </button>
          <button class="icon-btn" title="通知">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
          </button>
          <button class="icon-btn" title="设置">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </button>
        </div>

        <div class="user-menu">
          <div class="avatar">
            <span class="avatar-text">{{ username.charAt(0).toUpperCase() }}</span>
          </div>
          <div class="user-details">
            <span class="user-name">{{ username }}</span>
            <span class="user-role-badge" :class="role">{{ role === 'admin' ? '管理员' : '用户' }}</span>
          </div>
        </div>
      </div>
    </header>
    
    <div class="layout">
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <nav class="nav-menu">
          <a class="nav-item active">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="7" height="7" rx="1"/>
                <rect x="14" y="3" width="7" height="7" rx="1"/>
                <rect x="3" y="14" width="7" height="7" rx="1"/>
                <rect x="14" y="14" width="7" height="7" rx="1"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">数据总览</span>
          </a>
          <a class="nav-item">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">分类分析</span>
          </a>
          <a class="nav-item">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">借阅分析</span>
          </a>
          <a class="nav-item">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">用户分析</span>
          </a>
          <a class="nav-item">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
                <polyline points="17 6 23 6 23 12"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">趋势分析</span>
          </a>
          <a class="nav-item">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                <line x1="12" y1="6" x2="12" y2="12"/>
                <line x1="9" y1="9" x2="15" y2="9"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">图书分析</span>
          </a>
          <a class="nav-item">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">预测中心</span>
          </a>
          <a class="nav-item">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">数据报表</span>
          </a>
          <a class="nav-item">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">系统管理</span>
          </a>
        </nav>
        
        <div class="sidebar-footer" :class="{ hidden: sidebarCollapsed }">
          <div class="version-badge">v1.0.0</div>
        </div>
      </aside>
      
      <main class="main-content" :class="{ expanded: sidebarCollapsed }">
        <div v-if="!dataLoaded" class="loading-overlay">
          <div class="loading-spinner"></div>
          <span class="loading-text">正在加载数据...</span>
        </div>
        <OverviewView v-else :all-data="allData" />
      </main>
    </div>
  </div>
</template>

<style scoped src="./DashboardView.css"></style>
