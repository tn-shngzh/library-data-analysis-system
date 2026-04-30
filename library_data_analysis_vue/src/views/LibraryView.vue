<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { libraryApi } from '@/api/library'
import { useAuth } from '@/composables/useAuth'
import { useTime } from '@/composables/useTime'
import { useDropdown } from '@/composables/useDropdown'
import { useSearch } from '@/composables/useSearch'
import { useToast } from '@/composables/useToast'
import { getCache, setCache } from '@/utils/cache'

const { t } = useI18n()
const router = useRouter()
const { username, role, checkAuth, logout } = useAuth()
const { currentTime } = useTime()
const { showDropdown, dropdownRef: userMenuRef, toggleDropdown, closeDropdown } = useDropdown()
const { searchKeyword, searchResults, searchLoading: isSearching, performSearch, resetSearch } = useSearch()
const { showToast } = useToast()

const dataLoaded = ref(false)
const loadError = ref(false)
const activeTab = ref('home')
const loadingStats = ref(false)

const libraryData = reactive({
  stats: null,
  hotBooks: null,
  recentBorrows: null,
  categories: null,
  myBorrows: null
})

const tabs = ref([])

const updateTabs = () => {
  const baseTabs = [
    { id: 'home', label: t('library.tabHome'), icon: 'home' },
    { id: 'search', label: t('library.tabSearch'), icon: 'search' },
    { id: 'hot', label: t('library.tabHot'), icon: 'fire' }
  ]
  
  if (role.value !== 'admin') {
    baseTabs.push({ id: 'mybooks', label: t('library.tabMyBooks'), icon: 'books' })
  }
  
  tabs.value = baseTabs
}

const goToSettings = () => {
  showDropdown.value = false
  router.push('/settings')
}

const goToMyBooks = () => {
  showDropdown.value = false
  activeTab.value = 'mybooks'
}

const goToHotBooks = () => {
  showDropdown.value = false
  activeTab.value = 'hot'
}

const preloadData = async () => {
  const cached = getCache('libraryData')
  if (cached) {
    libraryData.stats = cached.stats
    libraryData.hotBooks = cached.hotBooks
    libraryData.recentBorrows = cached.recentBorrows
    libraryData.categories = cached.categories
    dataLoaded.value = true
    return
  }
  
  loadingStats.value = true
  loadError.value = false
  
  const results = {}
  const endpoints = {
    stats: '/api/borrows/stats',
    hotBooks: '/api/books/hot',
    recentBorrows: '/api/borrows/recent',
    categories: '/api/books/categories'
  }
  
  for (const [key, endpoint] of Object.entries(endpoints)) {
    try {
      console.log(`[Library] Loading ${key} from ${endpoint}`)
      const res = await fetch(endpoint)
      if (res.ok) {
        const data = await res.json()
        results[key] = data
        console.log(`[Library] ${key} loaded successfully`)
      } else {
        console.warn(`[Library] Failed to load ${key}: ${res.status}`)
      }
    } catch (e) {
      console.error(`[Library] Error loading ${key}:`, e)
    }
  }
  
  libraryData.stats = results.stats || null
  libraryData.hotBooks = results.hotBooks || null
  libraryData.recentBorrows = results.recentBorrows || null
  libraryData.categories = results.categories || null

  setCache('libraryData', {
    stats: libraryData.stats,
    hotBooks: libraryData.hotBooks,
    recentBorrows: libraryData.recentBorrows,
    categories: libraryData.categories
  })
  
  loadingStats.value = false
  dataLoaded.value = true
  
  const successCount = Object.keys(results).length
  const totalCount = Object.keys(endpoints).length
  if (successCount === 0) {
    loadError.value = true
    console.error('[Library] All endpoints failed to load')
  } else if (successCount < totalCount) {
    console.warn(`[Library] Only ${successCount}/${totalCount} endpoints loaded successfully`)
  }
}

const retryLoad = async () => {
  loadError.value = false
  await preloadData()
}

const loadMyBorrows = async () => {
  const cached = getCache('myBorrows', 5 * 60 * 1000)
  if (cached) {
    libraryData.myBorrows = cached
    return
  }
  
  try {
    const res = await libraryApi.getMyBorrows()
    if (res.ok) {
      const data = await res.json()
      libraryData.myBorrows = data
      setCache('myBorrows', data, 5 * 60 * 1000)
    }
  } catch (e) {
    console.error('加载借阅记录失败', e)
    if (cached) {
      libraryData.myBorrows = cached
    }
  }
}

const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    resetSearch()
    return
  }
  await performSearch()
}

const handleBorrow = async (bookId) => {
  try {
    const res = await libraryApi.borrowBook(bookId)
    if (res.ok) {
      const result = await res.json()
      if (result.success) {
        showToast(t('library.borrowSuccess'))
        preloadData()
        loadMyBorrows()
      }
    } else {
      const err = await res.json()
      showToast(err.detail || t('library.borrowFailed'), 'error')
    }
  } catch (e) {
    showToast(t('library.networkError'), 'error')
  }
}

const handleReturn = async (bookId) => {
  try {
    const res = await libraryApi.returnBook(bookId)
    if (res.ok) {
      const result = await res.json()
      if (result.success) {
        showToast(t('library.returnSuccess'))
        preloadData()
        loadMyBorrows()
      } else {
        showToast(result.detail || t('library.returnFailed'), 'error')
      }
    } else {
      const err = await res.json()
      showToast(err.detail || t('library.returnFailed'), 'error')
    }
  } catch (e) {
    showToast(t('library.returnFailed'), 'error')
  }
}

const handleRenew = async (bookId) => {
  try {
    const res = await libraryApi.renewBook(bookId)
    if (res.ok) {
      const result = await res.json()
      if (result.success) {
        showToast(t('library.renewSuccess'))
        loadMyBorrows()
      } else {
        showToast(result.detail || t('library.renewFailed'), 'error')
      }
    } else {
      const err = await res.json()
      showToast(err.detail || t('library.renewFailed'), 'error')
    }
  } catch (e) {
    showToast(t('library.renewFailed'), 'error')
  }
}

const handleTabChange = (tabId) => {
  activeTab.value = tabId
  if (tabId === 'mybooks' && !libraryData.myBorrows) {
    loadMyBorrows()
  }
}

onMounted(async () => {
  if (!checkAuth()) return
  updateTabs()
  await preloadData()
})
</script>

<template>
  <div class="library-system">
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
            <h1>{{ t('library.systemTitle') }}</h1>
            <span class="subtitle">{{ t('library.systemSubtitle') }}</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <div class="datetime">
          <span class="date">{{ currentTime }}</span>
        </div>
        <div class="user-menu" ref="userMenuRef">
          <div class="avatar" @click.stop="toggleDropdown">
            <span class="avatar-text">{{ username.charAt(0).toUpperCase() }}</span>
          </div>
          <div class="user-details" @click.stop="toggleDropdown">
            <span class="user-name">{{ username }}</span>
            <span class="user-role-badge user">{{ t('common.user') }}</span>
          </div>
          
          <transition name="dropdown">
            <div v-if="showDropdown" class="dropdown-menu">
              <div class="dropdown-header">
                <div class="dropdown-avatar">
                  <span>{{ username.charAt(0).toUpperCase() }}</span>
                </div>
                <div class="dropdown-user-info">
                  <div class="dropdown-username">{{ username }}</div>
                  <div class="dropdown-role">{{ t('library.normalUser') }}</div>
                </div>
              </div>
              
              <div class="dropdown-divider"></div>
              
              <div class="dropdown-body">
                <div class="dropdown-item" @click="goToSettings">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                  </svg>
                  <span>{{ t('library.userSettings') }}</span>
                </div>
                
                <div class="dropdown-item" v-if="role !== 'admin'" @click="goToMyBooks">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                  </svg>
                  <span>{{ t('library.tabMyBooks') }}</span>
                </div>
                
                <div class="dropdown-item" @click="goToHotBooks">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
                    <path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67z"/>
                  </svg>
                  <span>{{ t('library.tabHot') }}</span>
                </div>
              </div>
              
              <div class="dropdown-divider"></div>
              
              <div class="dropdown-footer">
                <div class="dropdown-item logout-item" @click="logout">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                    <polyline points="16 17 21 12 16 7"/>
                    <line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                  <span>{{ t('common.logout') }}</span>
                </div>
              </div>
            </div>
          </transition>
          
          <button @click="logout" class="logout-btn btn-icon btn-ghost" :title="t('common.logout')">
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
             @click="handleTabChange(tab.id)">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path v-if="tab.icon === 'home'" d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
                <circle v-if="tab.icon === 'search'" cx="11" cy="11" r="8"/>
                <line v-if="tab.icon === 'search'" x1="21" y1="21" x2="16.65" y2="16.65"/>
                <path v-if="tab.icon === 'fire'" d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67z"/>
                <path v-if="tab.icon === 'books'" d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path v-if="tab.icon === 'books'" d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
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
          <span class="loading-text">{{ t('library.loadingData') }}</span>
        </div>

        <div v-else-if="loadError" class="error-overlay">
          <svg viewBox="0 0 24 24" fill="currentColor" width="64" height="64" class="error-icon">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          <h3>{{ t('library.dataLoadFailed') }}</h3>
          <p>{{ t('library.someDataFailed') }}</p>
          <button @click="retryLoad" class="retry-btn btn btn-primary">
            <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
              <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
            </svg>
            {{ t('library.retry') }}
          </button>
        </div>

        <div v-else class="content-area">
          <div v-if="activeTab === 'home'" class="tab-content">
            <div class="welcome-banner">
              <div class="welcome-text">
                <h1>{{ t('library.welcomeBack', { name: username }) }}</h1>
                <p>{{ t('library.welcomeDesc') }}</p>
              </div>
              <div class="welcome-decoration">
                <svg viewBox="0 0 200 200" width="120" height="120">
                  <circle cx="100" cy="100" r="80" fill="rgba(217, 119, 6, 0.1)"/>
                  <circle cx="100" cy="100" r="60" fill="rgba(217, 119, 6, 0.15)"/>
                  <path d="M80 70h40v60H80z" fill="rgba(217, 119, 6, 0.3)" rx="4"/>
                  <path d="M85 75h30v50H85z" fill="rgba(217, 119, 6, 0.5)"/>
                </svg>
              </div>
            </div>

            <div class="stats-overview">
              <div class="stat-card primary">
                <div class="stat-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                    <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/>
                  </svg>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ libraryData.stats?.total_books || 0 }}</div>
                  <div class="stat-label">{{ t('library.statTotalBooks') }}</div>
                </div>
              </div>

              <div class="stat-card success">
                <div class="stat-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                  </svg>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ libraryData.stats?.borrowed_books || 0 }}</div>
                  <div class="stat-label">{{ t('library.statBorrowed') }}</div>
                </div>
              </div>

              <div class="stat-card warning">
                <div class="stat-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                    <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
                  </svg>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ libraryData.stats?.total_borrows || 0 }}</div>
                  <div class="stat-label">{{ t('library.statTotalBorrows') }}</div>
                </div>
              </div>

              <div class="stat-card info">
                <div class="stat-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                  </svg>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ libraryData.stats?.category_count || libraryData.categories?.length || 0 }}</div>
                  <div class="stat-label">{{ t('library.statCategories') }}</div>
                </div>
              </div>
            </div>

            <div v-if="role !== 'admin' && libraryData.stats?.my_borrows !== undefined" class="personal-stats">
              <h3 class="section-title">
                <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                  <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
                </svg>
                {{ t('library.myStats') }}
              </h3>
              <div class="stats-overview">
                <div class="stat-card personal">
                  <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                      <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/>
                    </svg>
                  </div>
                  <div class="stat-info">
                    <div class="stat-value">{{ libraryData.stats?.my_borrows || 0 }}</div>
                    <div class="stat-label">{{ t('library.statMyBorrows') }}</div>
                  </div>
                </div>

                <div class="stat-card personal">
                  <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                      <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
                    </svg>
                  </div>
                  <div class="stat-info">
                    <div class="stat-value">{{ libraryData.stats?.my_returns || 0 }}</div>
                    <div class="stat-label">{{ t('library.statMyReturns') }}</div>
                  </div>
                </div>

                <div class="stat-card personal">
                  <div class="stat-icon">
                    <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                      <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8 12.5v-9l6 4.5-6 4.5z"/>
                    </svg>
                  </div>
                  <div class="stat-info">
                    <div class="stat-value">{{ libraryData.stats?.my_current_borrowed || 0 }}</div>
                    <div class="stat-label">{{ t('library.statMyCurrentBorrowed') }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="home-grid">
              <div class="home-section">
                <h3 class="section-title">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                    <path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67z"/>
                  </svg>
                  {{ t('library.hotBooks') }}
                </h3>
                <div class="hot-books-list">
                  <div v-for="(book, index) in libraryData.hotBooks?.slice(0, 5)" :key="book.bib_id" class="hot-book-item">
                    <span class="hot-rank" :class="{ 'top3': index < 3 }">{{ index + 1 }}</span>
                    <div class="hot-book-info">
                      <div class="hot-book-title">{{ book.name }}</div>
                      <div class="hot-book-meta">
                        <span class="hot-book-category">{{ book.category }}</span>
                        <span class="hot-book-count">{{ t('library.borrowCount', { count: book.borrow_count }) }}</span>
                      </div>
                    </div>
                    <button v-if="role !== 'admin'" @click="handleBorrow(book.bib_id)" class="quick-borrow-btn btn btn-primary btn-sm">{{ t('library.borrow') }}</button>
                  </div>
                </div>
              </div>

              <div class="home-section" v-if="role !== 'admin'">
                <h3 class="section-title">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                    <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
                  </svg>
                  {{ t('library.recentBorrows') }}
                </h3>
                <div class="recent-borrows-list">
                  <div v-for="record in libraryData.recentBorrows?.slice(0, 8)" :key="record.date + record.borrower_id" class="recent-borrow-item">
                    <div class="recent-borrow-date">{{ record.date }}</div>
                    <div class="recent-borrow-info">
                      <span class="recent-borrow-action">{{ record.action }}</span>
                      <span class="recent-borrow-degree">{{ record.degree }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'search'" class="tab-content">
            <div class="search-container">
              <div class="search-header">
                <h2>{{ t('library.searchTitle') }}</h2>
                <p>{{ t('library.searchDesc') }}</p>
              </div>
              
              <div class="search-box">
                <input 
                  v-model="searchKeyword" 
                  type="text" 
                  :placeholder="t('library.searchPlaceholder')"
                  class="search-input"
                />
                <button @click="handleSearch" class="search-button btn btn-primary btn-lg" :disabled="isSearching">
                  <svg v-if="!isSearching" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                  </svg>
                  <div v-else class="search-loading"></div>
                  {{ isSearching ? t('library.searching') : t('library.searchBtn') }}
                </button>
              </div>

              <div v-if="searchResults.length > 0" class="search-results">
                <div class="results-header">
                  <span>{{ t('library.searchResultCount', { count: searchResults.length }) }}</span>
                  <span class="search-hint">{{ t('library.searchHint') }}</span>
                </div>
                <div class="results-grid">
                  <div v-for="book in searchResults" :key="book.bib_id" class="result-card">
                    <div class="result-card-header">
                      <div class="result-icon">
                        <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
                          <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/>
                        </svg>
                      </div>
                      <div class="result-title">{{ book.name }}</div>
                    </div>
                    <div class="result-card-body">
                      <span class="result-category">{{ book.category }}</span>
                      <span class="result-count">{{ t('library.borrowCount', { count: book.borrow_count }) }}</span>
                    </div>
                    <button v-if="role !== 'admin'" @click="handleBorrow(book.bib_id)" class="result-borrow-btn btn btn-primary btn-sm">{{ t('library.borrowNow') }}</button>
                  </div>
                </div>
              </div>

              <div v-else-if="searchKeyword && !isSearching" class="search-empty">
                <svg viewBox="0 0 24 24" fill="currentColor" width="64" height="64" class="empty-icon">
                  <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
                <p>{{ t('library.noResults') }}</p>
                <p class="empty-hint">{{ t('library.noResultsHint') }}</p>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'hot'" class="tab-content">
            <div class="hot-container">
              <div class="hot-header">
                <h2>{{ t('library.hotBooksRanking') }}</h2>
                <p>{{ t('library.hotBooksRankingDesc') }}</p>
              </div>

              <div class="hot-books-grid">
                <div v-for="(book, index) in libraryData.hotBooks" :key="book.bib_id" class="hot-book-card">
                  <div class="hot-card-rank" :class="{ 'top3': index < 3 }">
                    <span>{{ index + 1 }}</span>
                  </div>
                  <div class="hot-card-content">
                    <div class="hot-card-title">{{ book.name }}</div>
                    <div class="hot-card-meta">
                      <span class="hot-card-category">{{ book.category }}</span>
                    </div>
                    <div class="hot-card-stats">
                      <div class="hot-stat">
                        <span class="hot-stat-value">{{ book.borrow_count }}</span>
                        <span class="hot-stat-label">{{ t('library.borrowCountShort') }}</span>
                      </div>
                    </div>
                    <button v-if="role !== 'admin'" @click="handleBorrow(book.bib_id)" class="hot-borrow-btn btn btn-primary btn-sm">
                      <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                      </svg>
                      {{ t('library.borrow') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-if="activeTab === 'mybooks'" class="tab-content">
            <div class="mybooks-container">
              <div class="mybooks-header">
                <h2>{{ role === 'admin' ? t('library.allBorrowRecords') : t('library.myBorrowRecords') }}</h2>
                <p>{{ role === 'admin' ? t('library.allBorrowRecordsDesc') : t('library.myBorrowRecordsDesc') }}</p>
              </div>

              <div v-if="libraryData.myBorrows && libraryData.myBorrows.length > 0" class="mybooks-list">
                <div v-for="record in libraryData.myBorrows" :key="record.bib_id + record.date + record.time" class="mybook-item">
                  <div class="mybook-icon" :class="record.action === 'CKO' ? 'borrow' : 'return'">
                    <svg v-if="record.action === 'CKO'" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                      <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                    </svg>
                    <svg v-else viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                      <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                    </svg>
                  </div>
                  <div class="mybook-info">
                    <div class="mybook-title">{{ record.title }}</div>
                    <div class="mybook-meta">
                      <span class="mybook-category">{{ record.category }}</span>
                      <span class="mybook-action" :class="record.action === 'CKO' ? 'borrow' : 'return'">{{ record.action === 'CKO' ? t('library.checkout') : t('library.return') }}</span>
                      <span v-if="role === 'admin' && record.borrower" class="mybook-borrower">{{ record.borrower }}</span>
                    </div>
                  </div>
                  <div class="mybook-date">
                    <div class="mybook-date-value">{{ record.date }}</div>
                    <div class="mybook-time">{{ record.time }}</div>
                  </div>
                  <div v-if="record.action === 'CKO' && role !== 'admin'" class="mybook-actions">
                    <button class="action-btn return-btn btn btn-danger btn-sm" @click="handleReturn(record.bib_id)">{{ t('library.returnBook') }}</button>
                    <button class="action-btn renew-btn" @click="handleRenew(record.bib_id)">{{ t('library.renewBook') }}</button>
                  </div>
                </div>
              </div>

              <div v-else class="mybooks-empty">
                <svg viewBox="0 0 24 24" fill="currentColor" width="80" height="80" class="empty-icon">
                  <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/>
                </svg>
                <h3>{{ t('library.noBorrowRecords') }}</h3>
                <p>{{ role === 'admin' ? t('library.noBorrowRecordsAdmin') : t('library.noBorrowRecordsUser') }}</p>
                <button @click="activeTab = 'search'" class="go-search-btn btn btn-primary btn-sm">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                  </svg>
                  {{ t('library.goBorrow') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.library-system {
  min-height: 100vh;
  background: var(--gradient-surface);
  font-family: var(--font-sans);
}

.header {
  background: var(--gradient-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 0 var(--space-8);
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: var(--header-height);
  box-shadow: var(--shadow-sm);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: var(--z-fixed);
  border-bottom: 1px solid var(--color-neutral-200);
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.logo-icon {
  width: 42px;
  height: 42px;
  background: var(--gradient-primary);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-primary);
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
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  margin: 0;
  letter-spacing: var(--tracking-tight);
}

.subtitle {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
  font-weight: var(--font-medium);
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.datetime {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.date {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  font-weight: var(--font-medium);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3) var(--space-2) var(--space-2);
  background: var(--color-neutral-50);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-neutral-200);
  position: relative;
}

.avatar {
  width: 36px;
  height: 36px;
  background: var(--gradient-primary);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-primary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.avatar:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-primary-lg);
}

.avatar-text {
  color: white;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  cursor: pointer;
  transition: opacity var(--transition-base);
}

.user-details:hover {
  opacity: 0.8;
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-800);
}

.user-role-badge {
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.user-role-badge.user {
  color: var(--color-success-500);
  background: var(--color-success-50);
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 260px;
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-neutral-200);
  overflow: hidden;
  z-index: var(--z-dropdown);
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background: var(--gradient-surface);
  border-bottom: 1px solid var(--color-neutral-200);
}

.dropdown-avatar {
  width: 40px;
  height: 40px;
  background: var(--gradient-primary);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dropdown-avatar span {
  color: white;
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
}

.dropdown-user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.dropdown-username {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-800);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-role {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}

.dropdown-divider {
  height: 1px;
  background: var(--color-neutral-200);
}

.dropdown-body {
  padding: var(--space-2) 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 10px var(--space-4);
  cursor: pointer;
  transition: all var(--transition-fast);
  color: var(--color-neutral-600);
  font-size: var(--text-sm);
}

.dropdown-item:hover {
  background: var(--color-neutral-50);
  color: var(--color-primary-500);
}

.dropdown-item:active {
  background: var(--color-neutral-100);
}

.dropdown-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.dropdown-footer {
  padding: var(--space-2) 0;
}

.logout-item {
  color: var(--color-danger-500);
}

.logout-item:hover {
  background: var(--color-danger-50);
  color: var(--color-danger-600);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all var(--transition-base);
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}

.logout-btn svg {
  width: 18px;
  height: 18px;
}

.layout {
  display: flex;
  padding-top: var(--header-height);
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--gradient-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid var(--color-neutral-200);
  position: fixed;
  top: var(--header-height);
  bottom: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  z-index: var(--z-sticky);
}

.nav-menu {
  flex: 1;
  padding: var(--space-4) var(--space-3);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 12px var(--space-4);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-base);
  position: relative;
  color: var(--color-neutral-500);
  text-decoration: none;
}

.nav-item:hover {
  background: var(--color-primary-50);
  color: var(--color-primary-500);
}

.nav-item.active {
  background: var(--color-primary-50);
  color: var(--color-primary-500);
  font-weight: var(--font-semibold);
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
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.nav-indicator {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--gradient-primary);
  border-radius: 2px;
}

.sidebar-footer {
  padding: var(--space-4);
  border-top: 1px solid var(--color-neutral-200);
  text-align: center;
}

.version-badge {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
  font-weight: var(--font-medium);
}

.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding: var(--space-6) var(--space-8);
  min-height: calc(100vh - var(--header-height));
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
  color: var(--color-neutral-500);
  font-size: var(--text-sm);
}

.error-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: var(--space-4);
  text-align: center;
}

.error-icon {
  color: var(--color-warning-400);
}

.error-overlay h3 {
  color: var(--color-neutral-800);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  margin: 0;
}

.error-overlay p {
  color: var(--color-neutral-500);
  font-size: var(--text-sm);
  margin: 0;
  max-width: 400px;
}

.retry-btn svg {
  animation: spin 1s linear infinite;
}

.content-area {
  max-width: 1200px;
  margin: 0 auto;
}

.tab-content {
  animation: fadeInUp 0.3s ease;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.welcome-banner {
  background: var(--gradient-primary);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  margin-bottom: var(--space-6);
  box-shadow: var(--shadow-primary-lg);
}

.welcome-text h1 {
  margin: 0 0 var(--space-2) 0;
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
}

.welcome-text p {
  margin: 0;
  opacity: 0.9;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.stat-card {
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  align-items: center;
  gap: var(--space-4);
  box-shadow: var(--shadow-sm);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card.primary .stat-icon {
  background: var(--color-primary-50);
  color: var(--color-primary-500);
}

.stat-card.success .stat-icon {
  background: var(--color-success-50);
  color: var(--color-success-500);
}

.stat-card.warning .stat-icon {
  background: var(--color-warning-50);
  color: var(--color-warning-500);
}

.stat-card.info .stat-icon {
  background: var(--color-info-50);
  color: var(--color-info-500);
}

.stat-card.personal .stat-icon {
  background: rgba(217, 119, 6, 0.1);
  color: var(--color-warning-500);
}

.personal-stats {
  margin-bottom: var(--space-6);
}

.personal-stats .section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
  color: var(--color-neutral-800);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin-top: var(--space-1);
}

.home-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-6);
}

.home-section {
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin: 0 0 var(--space-4) 0;
  color: var(--color-neutral-900);
  font-size: var(--text-base);
}

.hot-books-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.hot-book-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-neutral-50);
  border-radius: var(--radius-lg);
  transition: background var(--transition-base);
}

.hot-book-item:hover {
  background: var(--color-neutral-100);
}

.hot-rank {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  background: var(--color-neutral-200);
  color: var(--color-neutral-500);
  flex-shrink: 0;
}

.hot-rank.top3 {
  background: var(--gradient-primary);
  color: white;
}

.hot-book-info {
  flex: 1;
  min-width: 0;
}

.hot-book-title {
  font-weight: var(--font-medium);
  color: var(--color-neutral-800);
  font-size: var(--text-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-book-meta {
  display: flex;
  gap: var(--space-3);
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  margin-top: var(--space-1);
}

.quick-borrow-btn {
  flex-shrink: 0;
}

.recent-borrows-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.recent-borrow-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--color-neutral-50);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.recent-borrow-date {
  color: var(--color-neutral-400);
  font-size: var(--text-xs);
  flex-shrink: 0;
  width: 80px;
}

.recent-borrow-info {
  display: flex;
  gap: var(--space-3);
  flex: 1;
}

.recent-borrow-action {
  color: var(--color-primary-500);
  font-weight: var(--font-medium);
}

.recent-borrow-degree {
  color: var(--color-neutral-500);
}

.search-container, .hot-container, .mybooks-container {
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
  padding: var(--space-8);
  box-shadow: var(--shadow-sm);
}

.search-header, .hot-header, .mybooks-header {
  text-align: center;
  margin-bottom: var(--space-8);
}

.search-header h2, .hot-header h2, .mybooks-header h2 {
  margin: 0 0 var(--space-2) 0;
  color: var(--color-neutral-900);
}

.search-header p, .hot-header p, .mybooks-header p {
  margin: 0;
  color: var(--color-neutral-500);
}

.search-box {
  display: flex;
  gap: var(--space-4);
  max-width: 700px;
  margin: 0 auto var(--space-8);
}

.search-input {
  flex: 1;
  padding: 14px var(--space-5);
  border: 2px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  outline: none;
  transition: border-color var(--transition-base), box-shadow var(--transition-base);
  background: var(--color-neutral-50);
}

.search-input:focus {
  border-color: var(--color-primary-500);
  background: var(--color-neutral-0);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.search-loading {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

.results-header {
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-neutral-200);
  margin-bottom: var(--space-4);
  color: var(--color-neutral-500);
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

.search-hint {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
  font-style: italic;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

.result-card {
  background: var(--color-neutral-50);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  transition: all var(--transition-base);
}

.result-card:hover {
  background: var(--color-neutral-100);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.result-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.result-icon {
  width: 40px;
  height: 40px;
  background: var(--color-primary-50);
  color: var(--color-primary-500);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.result-title {
  font-weight: var(--font-semibold);
  color: var(--color-neutral-800);
  font-size: var(--text-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-card-body {
  display: flex;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
}

.result-borrow-btn {
  width: 100%;
}

.search-empty {
  text-align: center;
  padding: var(--space-12) 0;
  color: var(--color-neutral-400);
}

.empty-icon {
  color: var(--color-neutral-200);
  margin-bottom: var(--space-4);
}

.empty-hint {
  font-size: var(--text-sm);
  margin-top: var(--space-2);
}

.hot-books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-4);
}

.hot-book-card {
  background: var(--color-neutral-50);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  display: flex;
  gap: var(--space-4);
  transition: all var(--transition-base);
}

.hot-book-card:hover {
  background: var(--color-neutral-100);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.hot-card-rank {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: var(--font-bold);
  background: var(--color-neutral-200);
  color: var(--color-neutral-500);
  flex-shrink: 0;
}

.hot-card-rank.top3 {
  background: var(--gradient-primary);
  color: white;
}

.hot-card-content {
  flex: 1;
  min-width: 0;
}

.hot-card-title {
  font-weight: var(--font-semibold);
  color: var(--color-neutral-800);
  font-size: var(--text-sm);
  margin-bottom: var(--space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-card-meta {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
  margin-bottom: var(--space-2);
}

.hot-card-stats {
  margin-bottom: var(--space-3);
}

.hot-stat {
  display: flex;
  align-items: baseline;
  gap: var(--space-1);
}

.hot-stat-value {
  font-size: var(--text-xl);
  font-weight: var(--font-bold);
  color: var(--color-primary-500);
}

.hot-stat-label {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
}

.hot-borrow-btn {
  width: 100%;
  gap: var(--space-1);
}

.mybooks-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.mybook-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-neutral-50);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
}

.mybook-item:hover {
  background: var(--color-neutral-100);
}

.mybook-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.mybook-icon.borrow {
  background: var(--color-primary-50);
  color: var(--color-primary-500);
}

.mybook-icon.return {
  background: var(--color-success-50);
  color: var(--color-success-500);
}

.mybook-info {
  flex: 1;
  min-width: 0;
}

.mybook-title {
  font-weight: var(--font-medium);
  color: var(--color-neutral-800);
  margin-bottom: var(--space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mybook-meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.mybook-category {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
}

.mybook-action {
  font-size: var(--text-xs);
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  font-weight: var(--font-medium);
}

.mybook-action.borrow {
  background: var(--color-primary-50);
  color: var(--color-primary-500);
}

.mybook-action.return {
  background: var(--color-success-50);
  color: var(--color-success-500);
}

.mybook-borrower {
  font-size: var(--text-xs);
  padding: 2px var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--color-warning-50);
  color: var(--color-warning-500);
  font-weight: var(--font-medium);
}

.mybook-date {
  text-align: right;
  flex-shrink: 0;
}

.mybook-date-value {
  font-size: var(--text-sm);
  color: var(--color-neutral-800);
  font-weight: var(--font-medium);
}

.mybook-time {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
}

.mybook-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.action-btn {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  border: none;
  margin-right: 4px;
}

.renew-btn {
  background: var(--color-info-500);
  color: var(--color-neutral-0);
}

.mybooks-empty {
  text-align: center;
  padding: var(--space-12) 0;
  color: var(--color-neutral-400);
}

.mybooks-empty h3 {
  color: var(--color-neutral-500);
  margin: var(--space-4) 0 var(--space-2);
}

.mybooks-empty p {
  margin: 0 0 var(--space-6);
}

@media (max-width: 1024px) {
  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: var(--sidebar-collapsed-width);
  }

  .sidebar .nav-label,
  .sidebar .nav-footer {
    display: none;
  }

  .main-content {
    margin-left: var(--sidebar-collapsed-width);
    padding: var(--space-4);
  }

  .home-grid {
    grid-template-columns: 1fr;
  }

  .search-box {
    flex-direction: column;
  }

  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
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

  .stats-overview {
    grid-template-columns: 1fr;
  }

  .welcome-banner {
    padding: var(--space-5);
    flex-direction: column;
    text-align: center;
  }
}
</style>