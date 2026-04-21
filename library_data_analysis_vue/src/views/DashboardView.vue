<script setup>
import { ref, onMounted, markRaw, reactive } from 'vue'
import OverviewView from './OverviewView.vue'
import ReaderView from './ReaderView.vue'
import BookView from './BookView.vue'
import BorrowView from './BorrowView.vue'
import { overviewApi } from '@/api/overview'
import { readerApi } from '@/api/readers'
import { bookApi } from '@/api/books'
import { borrowApi } from '@/api/borrows'
import { useAuth } from '@/composables/useAuth'
import { useTime } from '@/composables/useTime'

const { username, role, checkAuth, logout } = useAuth()
const { currentTime } = useTime()

const activeTab = ref('overview')
const dataLoaded = ref(false)
const sidebarCollapsed = ref(false)

const tabs = ref([])

const updateTabs = () => {
  const baseTabs = [
    { id: 'overview', label: '总览', icon: 'grid', component: markRaw(OverviewView) },
    { id: 'readers', label: '读者', icon: 'users', component: markRaw(ReaderView) },
    { id: 'books', label: '图书', icon: 'book', component: markRaw(BookView) }
  ]
  
  if (role.value !== 'admin') {
    baseTabs.push({ id: 'borrows', label: '借阅', icon: 'arrow', component: markRaw(BorrowView) })
  }
  
  tabs.value = baseTabs
}

const overviewData = reactive({
  stats: null,
  categories: null,
  recentBooks: null
})

const readerData = reactive({
  stats: null,
  readerTypes: null,
  monthlyTrend: null,
  topReaders: null
})

const bookData = reactive({
  stats: null,
  categories: null,
  hotBooks: null
})

const borrowData = reactive({
  stats: null,
  actionStats: null,
  degreeStats: null,
  topBorrowers: null,
  topBooks: null,
  recentBorrows: null
})

const preloadData = async () => {
  try {
    const [overviewResult, readerResult, bookResult, borrowResult] = await Promise.all([
      overviewApi.getAll(),
      readerApi.getAll(),
      bookApi.getAll(),
      borrowApi.getAll()
    ])

    if (overviewResult.stats) overviewData.stats = overviewResult.stats
    if (overviewResult.categories) overviewData.categories = overviewResult.categories
    if (overviewResult.recentBooks) overviewData.recentBooks = overviewResult.recentBooks

    if (readerResult.stats) readerData.stats = readerResult.stats
    if (readerResult.readerTypes) readerData.readerTypes = readerResult.readerTypes
    if (readerResult.monthlyTrend) readerData.monthlyTrend = readerResult.monthlyTrend
    if (readerResult.topReaders) readerData.topReaders = readerResult.topReaders

    if (bookResult.stats) bookData.stats = bookResult.stats
    if (bookResult.categories) bookData.categories = bookResult.categories
    if (bookResult.hotBooks) bookData.hotBooks = bookResult.hotBooks

    if (borrowResult.stats) borrowData.stats = borrowResult.stats
    if (borrowResult.actionStats) borrowData.actionStats = borrowResult.actionStats
    if (borrowResult.degreeStats) borrowData.degreeStats = borrowResult.degreeStats
    if (borrowResult.topBorrowers) borrowData.topBorrowers = borrowResult.topBorrowers
    if (borrowResult.topBooks) borrowData.topBooks = borrowResult.topBooks
    if (borrowResult.recentBorrows) borrowData.recentBorrows = borrowResult.recentBorrows

    dataLoaded.value = true
  } catch (e) {
    console.error('预加载数据失败', e)
    dataLoaded.value = true
  }
}

onMounted(async () => {
  if (!checkAuth()) return
  updateTabs()
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
          <div class="title-group" :class="{ hidden: sidebarCollapsed }">
            <h1>图书馆数据分析系统</h1>
            <span class="subtitle">Library Data Analytics</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <div class="datetime">
          <span class="date">{{ currentTime }}</span>
        </div>
        <div class="user-menu">
          <div class="avatar">
            <span class="avatar-text">{{ username.charAt(0).toUpperCase() }}</span>
          </div>
          <div class="user-details" :class="{ hidden: sidebarCollapsed }">
            <span class="user-name">{{ username }}</span>
            <span class="user-role-badge" :class="role">{{ role === 'admin' ? '管理员' : '用户' }}</span>
          </div>
          <button @click="logout" class="logout-btn" title="退出登录">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </div>
    </header>
    
    <div class="layout">
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <nav class="nav-menu">
          <a v-for="tab in tabs" :key="tab.id" 
             class="nav-item" 
             :class="{ active: activeTab === tab.id }"
             @click="activeTab = tab.id">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect v-if="tab.icon === 'grid'" x="3" y="3" width="7" height="7" rx="1"/>
                <rect v-if="tab.icon === 'grid'" x="14" y="3" width="7" height="7" rx="1"/>
                <rect v-if="tab.icon === 'grid'" x="3" y="14" width="7" height="7" rx="1"/>
                <rect v-if="tab.icon === 'grid'" x="14" y="14" width="7" height="7" rx="1"/>
                <path v-if="tab.icon === 'users'" d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle v-if="tab.icon === 'users'" cx="9" cy="7" r="4"/>
                <path v-if="tab.icon === 'users'" d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path v-if="tab.icon === 'users'" d="M16 3.13a4 4 0 0 1 0 7.75"/>
                <path v-if="tab.icon === 'book'" d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path v-if="tab.icon === 'book'" d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                <line v-if="tab.icon === 'arrow'" x1="12" y1="5" x2="12" y2="19"/>
                <polyline v-if="tab.icon === 'arrow'" points="19 12 12 19 5 12"/>
              </svg>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">{{ tab.label }}</span>
          </a>
        </nav>
        
        <div class="sidebar-footer" :class="{ hidden: sidebarCollapsed }">
          <div class="version-badge">v0.10.0</div>
        </div>
      </aside>
      
      <main class="main-content" :class="{ expanded: sidebarCollapsed }">
        <div v-if="!dataLoaded" class="loading-overlay">
          <div class="loading-spinner"></div>
          <span class="loading-text">正在加载数据...</span>
        </div>
        <transition v-else name="fade" mode="out-in">
          <component 
            :is="tabs.find(t => t.id === activeTab)?.component" 
            :key="activeTab"
            :preloaded-data="activeTab === 'overview' ? overviewData : activeTab === 'readers' ? readerData : activeTab === 'books' ? bookData : borrowData"
          />
        </transition>
      </main>
    </div>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: var(--color-neutral-50);
  font-family: var(--font-sans);
  color: var(--color-neutral-900);
}

.header {
  background: var(--gradient-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 0 var(--space-6);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: var(--header-height);
  border-bottom: 1px solid var(--color-neutral-200);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-fixed);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.sidebar-toggle {
  width: 36px;
  height: 36px;
  background: var(--color-neutral-100);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  color: var(--color-neutral-500);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.sidebar-toggle:hover {
  background: var(--color-neutral-200);
  color: var(--color-neutral-900);
}

.sidebar-toggle:active {
  transform: scale(0.92);
}

.sidebar-toggle svg {
  width: 18px;
  height: 18px;
  transition: transform var(--transition-base);
}

.sidebar-toggle.collapsed svg {
  transform: rotate(180deg);
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: var(--gradient-primary);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-primary);
}

.logo-icon svg {
  width: 20px;
  height: 20px;
  color: white;
}

.title-group {
  display: flex;
  flex-direction: column;
  gap: 1px;
  transition: opacity var(--transition-base);
}

.title-group.hidden {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.title-group h1 {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
  margin: 0;
  letter-spacing: var(--tracking-tight);
}

.subtitle {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.datetime {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.date {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-1) var(--space-3) var(--space-1) var(--space-1);
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-neutral-200);
}

.avatar {
  width: 32px;
  height: 32px;
  background: var(--gradient-primary);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-text {
  color: white;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 1px;
  transition: opacity var(--transition-base);
}

.user-details.hidden {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-900);
}

.user-role-badge {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.user-role-badge.admin {
  color: var(--color-primary-400);
  background: var(--color-primary-50);
}

.user-role-badge.user {
  color: var(--color-success-400);
  background: var(--color-success-50);
}

.logout-btn {
  width: 32px;
  height: 32px;
  background: transparent;
  color: var(--color-neutral-500);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-base);
}

.logout-btn svg {
  width: 16px;
  height: 16px;
}

.logout-btn:hover {
  background: var(--color-danger-50);
  color: var(--color-danger-400);
}

.layout {
  display: flex;
  padding-top: var(--header-height);
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--color-neutral-0);
  border-right: 1px solid var(--color-neutral-200);
  padding: var(--space-5) 0;
  position: fixed;
  top: var(--header-height);
  bottom: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  transition: width var(--transition-slow);
  overflow: hidden;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: 0 var(--space-3);
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  color: var(--color-neutral-500);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: all var(--transition-base);
  user-select: none;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 60%;
  background: var(--gradient-primary);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  transition: transform var(--transition-base);
}

.nav-item.active::before {
  transform: translateY(-50%) scaleY(1);
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.nav-icon svg {
  width: 20px;
  height: 20px;
}

.nav-label {
  flex: 1;
  transition: opacity var(--transition-base);
}

.nav-label.hidden {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.nav-item:hover {
  background: var(--color-neutral-100);
  color: var(--color-neutral-900);
}

.nav-item.active {
  background: var(--color-primary-50);
  color: var(--color-primary-500);
  border: 1px solid var(--color-primary-100);
}

.sidebar-footer {
  padding: var(--space-4);
  text-align: center;
  transition: opacity var(--transition-base);
}

.sidebar-footer.hidden {
  opacity: 0;
}

.version-badge {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
  padding: var(--space-1) var(--space-3);
  background: var(--color-neutral-100);
  border-radius: var(--radius-sm);
  display: inline-block;
}

.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding: var(--space-6);
  transition: margin-left var(--transition-slow);
  min-height: calc(100vh - var(--header-height));
}

.main-content.expanded {
  margin-left: var(--sidebar-collapsed-width);
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: var(--space-4);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-neutral-200);
  border-top-color: var(--color-primary-500);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
}

.fade-enter-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-3px);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 1024px) {
  .sidebar {
    width: var(--sidebar-collapsed-width);
  }

  .sidebar .nav-label,
  .sidebar .sidebar-footer {
    display: none;
  }

  .main-content {
    margin-left: var(--sidebar-collapsed-width);
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: var(--sidebar-collapsed-width);
  }

  .sidebar .nav-label,
  .sidebar .sidebar-footer {
    display: none;
  }

  .main-content {
    margin-left: var(--sidebar-collapsed-width);
    padding: var(--space-4);
  }

  .title-group {
    display: none;
  }

  .user-details {
    display: none;
  }

  .header-right .datetime {
    display: none;
  }
}

@media (max-width: 480px) {
  .header {
    padding: 0 var(--space-3);
  }

  .main-content {
    padding: var(--space-3);
  }
}
</style>