<script setup>
import { ref, onMounted, markRaw, reactive } from 'vue'
import { useRouter } from 'vue-router'
import OverviewView from './OverviewView.vue'
import ReaderView from './ReaderView.vue'
import BookView from './BookView.vue'
import BorrowView from './BorrowView.vue'

const router = useRouter()
const username = ref('')
const role = ref('')
const activeTab = ref('overview')
const currentTime = ref('')
const dataLoaded = ref(false)

const tabs = [
  { id: 'overview', label: '总览', icon: 'grid', component: markRaw(OverviewView) },
  { id: 'readers', label: '读者', icon: 'users', component: markRaw(ReaderView) },
  { id: 'books', label: '图书', icon: 'book', component: markRaw(BookView) },
  { id: 'borrows', label: '借阅', icon: 'arrow', component: markRaw(BorrowView) }
]

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

const updateTime = () => {
  const now = new Date()
  const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }
  currentTime.value = now.toLocaleDateString('zh-CN', options)
}

const preloadData = async () => {
  try {
    const [
      overviewStatsRes, overviewCatRes, overviewRecentRes,
      readerStatsRes, readerTypesRes, readerTrendRes, readerTopRes,
      bookStatsRes, bookCatRes, bookHotRes,
      borrowStatsRes, borrowActionRes, borrowDegreeRes, borrowTopBorrowersRes, borrowTopBooksRes, borrowRecentRes
    ] = await Promise.all([
      fetch('/api/overview/stats'),
      fetch('/api/overview/categories'),
      fetch('/api/overview/recent-books'),
      fetch('/api/readers/stats'),
      fetch('/api/readers/types'),
      fetch('/api/readers/monthly-trend'),
      fetch('/api/readers/top'),
      fetch('/api/books/stats'),
      fetch('/api/books/categories'),
      fetch('/api/books/hot'),
      fetch('/api/borrows/stats'),
      fetch('/api/borrows/action-stats'),
      fetch('/api/borrows/degree-stats'),
      fetch('/api/borrows/top-borrowers'),
      fetch('/api/borrows/top-books'),
      fetch('/api/borrows/recent')
    ])

    if (overviewStatsRes.ok) overviewData.stats = await overviewStatsRes.json()
    if (overviewCatRes.ok) overviewData.categories = await overviewCatRes.json()
    if (overviewRecentRes.ok) overviewData.recentBooks = await overviewRecentRes.json()

    if (readerStatsRes.ok) readerData.stats = await readerStatsRes.json()
    if (readerTypesRes.ok) readerData.readerTypes = await readerTypesRes.json()
    if (readerTrendRes.ok) readerData.monthlyTrend = await readerTrendRes.json()
    if (readerTopRes.ok) readerData.topReaders = await readerTopRes.json()

    if (bookStatsRes.ok) bookData.stats = await bookStatsRes.json()
    if (bookCatRes.ok) bookData.categories = await bookCatRes.json()
    if (bookHotRes.ok) bookData.hotBooks = await bookHotRes.json()

    if (borrowStatsRes.ok) borrowData.stats = await borrowStatsRes.json()
    if (borrowActionRes.ok) borrowData.actionStats = await borrowActionRes.json()
    if (borrowDegreeRes.ok) borrowData.degreeStats = await borrowDegreeRes.json()
    if (borrowTopBorrowersRes.ok) borrowData.topBorrowers = await borrowTopBorrowersRes.json()
    if (borrowTopBooksRes.ok) borrowData.topBooks = await borrowTopBooksRes.json()
    if (borrowRecentRes.ok) borrowData.recentBorrows = await borrowRecentRes.json()

    dataLoaded.value = true
  } catch (e) {
    console.error('预加载数据失败', e)
    dataLoaded.value = true
  }
}

onMounted(async () => {
  const token = localStorage.getItem('token')
  if (!token) {
    router.push('/login')
    return
  }
  
  username.value = localStorage.getItem('username') || ''
  role.value = localStorage.getItem('role') || ''
  updateTime()
  setInterval(updateTime, 60000)
  
  await preloadData()
})

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  router.push('/login')
}
</script>

<template>
  <div class="dashboard">
    <header class="header">
      <div class="header-left">
        <div class="logo-wrapper">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <div class="title-group">
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
          <div class="user-details">
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
      <aside class="sidebar">
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
            <span class="nav-label">{{ tab.label }}</span>
            <div class="nav-indicator" v-if="activeTab === tab.id"></div>
          </a>
        </nav>
        
        <div class="sidebar-footer">
          <div class="version-badge">v0.7.0</div>
        </div>
      </aside>
      
      <main class="main-content">
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
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e8ecf4 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.header {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 0 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 70px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 8px 24px rgba(0, 0, 0, 0.03);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  border-bottom: 1px solid rgba(226, 232, 240, 0.6);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-icon {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.logo-icon svg {
  width: 22px;
  height: 22px;
  color: white;
}

.title-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title-group h1 {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.datetime {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.date {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 12px 6px 6px;
  background: #f8fafc;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
}

.avatar {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
}

.avatar-text {
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.user-role-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.user-role-badge.admin {
  color: #6366f1;
  background: #eef2ff;
}

.user-role-badge.user {
  color: #10b981;
  background: #ecfdf5;
}

.logout-btn {
  width: 32px;
  height: 32px;
  background: transparent;
  color: #94a3b8;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.logout-btn svg {
  width: 18px;
  height: 18px;
}

.logout-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.layout {
  display: flex;
  padding-top: 70px;
  min-height: 100vh;
}

.sidebar {
  width: 220px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(226, 232, 240, 0.6);
  padding: 24px 0;
  position: fixed;
  top: 70px;
  bottom: 0;
  left: 0;
  display: flex;
  flex-direction: column;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 16px;
  flex: 1;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  color: #64748b;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  user-select: none;
  position: relative;
  overflow: hidden;
}

.nav-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon svg {
  width: 20px;
  height: 20px;
}

.nav-label {
  flex: 1;
}

.nav-item:hover {
  background: rgba(99, 102, 241, 0.06);
  color: #4f46e5;
  transform: translateX(2px);
}

.nav-item.active {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  transform: translateX(0);
}

.nav-indicator {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 2px;
}

.sidebar-footer {
  padding: 16px;
  text-align: center;
}

.version-badge {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
  background: #f1f5f9;
  padding: 4px 10px;
  border-radius: 6px;
  display: inline-block;
}

.main-content {
  flex: 1;
  margin-left: 220px;
  padding: 28px 32px;
  min-height: calc(100vh - 70px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 150px);
  gap: 20px;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-text {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
