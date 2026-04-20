<script setup>
import { ref, onMounted, reactive, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const role = ref('')
const currentTime = ref('')
const dataLoaded = ref(false)
const activeTab = ref('home')

const searchQuery = ref('')
const searchResults = ref([])
const isSearching = ref(false)

const showDropdown = ref(false)
const userMenuRef = ref(null)

const libraryData = reactive({
  stats: null,
  hotBooks: null,
  recentBorrows: null,
  categories: null,
  myBorrows: null
})

const tabs = [
  { id: 'home', label: '首页', icon: 'home' },
  { id: 'search', label: '图书检索', icon: 'search' },
  { id: 'hot', label: '热门图书', icon: 'fire' },
  { id: 'mybooks', label: '我的借阅', icon: 'books' }
]

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
}

const closeDropdown = (event) => {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target)) {
    showDropdown.value = false
  }
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

onMounted(() => {
  document.addEventListener('click', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})

// 防抖函数
const debounce = (fn, delay) => {
  let timer = null
  return function(...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

// 实时搜索函数
const performRealTimeSearch = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  try {
    const response = await fetch(`/api/books/search?keyword=${encodeURIComponent(searchQuery.value)}&page=1&page_size=20`)
    if (response.ok) {
      const data = await response.json()
      searchResults.value = data.books || []
    }
  } catch (e) {
    console.error('搜索失败', e)
  }
}

// 创建防抖的搜索函数（500ms 延迟）
const debouncedSearch = debounce(performRealTimeSearch, 500)

// 监听搜索框输入
watch(searchQuery, () => {
  if (activeTab.value === 'search') {
    debouncedSearch()
  }
})

const updateTime = () => {
  const now = new Date()
  const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' }
  currentTime.value = now.toLocaleDateString('zh-CN', options)
}

const preloadData = async () => {
  try {
    const [statsRes, hotBooksRes, recentRes, categoriesRes] = await Promise.all([
      fetch('/api/borrows/stats'),
      fetch('/api/books/hot'),
      fetch('/api/borrows/recent'),
      fetch('/api/books/categories')
    ])

    if (statsRes.ok) libraryData.stats = await statsRes.json()
    if (hotBooksRes.ok) libraryData.hotBooks = await hotBooksRes.json()
    if (recentRes.ok) libraryData.recentBorrows = await recentRes.json()
    if (categoriesRes.ok) libraryData.categories = await categoriesRes.json()

    dataLoaded.value = true
  } catch (e) {
    console.error('加载数据失败', e)
    dataLoaded.value = true
  }
}

const loadMyBorrows = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/borrows/my', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (response.ok) {
      libraryData.myBorrows = await response.json()
    }
  } catch (e) {
    console.error('加载借阅记录失败', e)
  }
}

const handleSearch = async () => {
  // 手动点击搜索按钮时，立即执行搜索，不使用防抖
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  isSearching.value = true
  try {
    const response = await fetch(`/api/books/search?keyword=${encodeURIComponent(searchQuery.value)}&page=1&page_size=50`)
    if (response.ok) {
      const data = await response.json()
      searchResults.value = data.books || []
    }
  } catch (e) {
    console.error('搜索失败', e)
  } finally {
    isSearching.value = false
  }
}

const handleBorrow = async (bookId) => {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/borrows/borrow', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ book_id: bookId })
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.success) {
        alert('借阅成功！')
        preloadData()
      }
    } else {
      const err = await response.json()
      alert(err.detail || '借阅失败')
    }
  } catch (e) {
    alert('网络错误，请重试')
  }
}

const handleTabChange = (tabId) => {
  activeTab.value = tabId
  if (tabId === 'mybooks' && !libraryData.myBorrows) {
    loadMyBorrows()
  }
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  router.push('/login')
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
            <h1>图书馆管理系统</h1>
            <span class="subtitle">Library Management System</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <div class="datetime">
          <span class="date">{{ currentTime }}</span>
        </div>
        <div class="user-menu" ref="userMenuRef">
          <div class="avatar" @click="toggleDropdown">
            <span class="avatar-text">{{ username.charAt(0).toUpperCase() }}</span>
          </div>
          <div class="user-details" @click="toggleDropdown">
            <span class="user-name">{{ username }}</span>
            <span class="user-role-badge user">用户</span>
          </div>
          
          <!-- 下拉菜单 -->
          <transition name="dropdown">
            <div v-if="showDropdown" class="dropdown-menu">
              <div class="dropdown-header">
                <div class="dropdown-avatar">
                  <span>{{ username.charAt(0).toUpperCase() }}</span>
                </div>
                <div class="dropdown-user-info">
                  <div class="dropdown-username">{{ username }}</div>
                  <div class="dropdown-role">普通用户</div>
                </div>
              </div>
              
              <div class="dropdown-divider"></div>
              
              <div class="dropdown-body">
                <div class="dropdown-item" @click="goToSettings">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                  </svg>
                  <span>用户设置</span>
                </div>
                
                <div class="dropdown-item" @click="goToMyBooks">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                  </svg>
                  <span>我的借阅</span>
                </div>
                
                <div class="dropdown-item" @click="goToHotBooks">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
                    <path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67z"/>
                  </svg>
                  <span>热门图书</span>
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
                  <span>退出登录</span>
                </div>
              </div>
            </div>
          </transition>
          
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
          <span class="loading-text">正在加载数据...</span>
        </div>

        <div v-else class="content-area">
          <!-- 首页 -->
          <div v-if="activeTab === 'home'" class="tab-content">
            <div class="welcome-banner">
              <div class="welcome-text">
                <h1>欢迎回来，{{ username }}！</h1>
                <p>今天也是充满书香的一天</p>
              </div>
              <div class="welcome-decoration">
                <svg viewBox="0 0 200 200" width="120" height="120">
                  <circle cx="100" cy="100" r="80" fill="rgba(99, 102, 241, 0.1)"/>
                  <circle cx="100" cy="100" r="60" fill="rgba(99, 102, 241, 0.15)"/>
                  <path d="M80 70h40v60H80z" fill="rgba(99, 102, 241, 0.3)" rx="4"/>
                  <path d="M85 75h30v50H85z" fill="rgba(99, 102, 241, 0.5)"/>
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
                  <div class="stat-label">馆藏总量</div>
                </div>
              </div>

              <div class="stat-card success">
                <div class="stat-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                  </svg>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ libraryData.stats?.cko_count || 0 }}</div>
                  <div class="stat-label">在借图书</div>
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
                  <div class="stat-label">总借阅次数</div>
                </div>
              </div>

              <div class="stat-card info">
                <div class="stat-icon">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                    <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
                  </svg>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ libraryData.categories?.length || 0 }}</div>
                  <div class="stat-label">图书分类</div>
                </div>
              </div>
            </div>

            <div class="home-grid">
              <div class="home-section">
                <h3 class="section-title">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                    <path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67z"/>
                  </svg>
                  热门图书
                </h3>
                <div class="hot-books-list">
                  <div v-for="(book, index) in libraryData.hotBooks?.slice(0, 5)" :key="book.bib_id" class="hot-book-item">
                    <span class="hot-rank" :class="{ 'top3': index < 3 }">{{ index + 1 }}</span>
                    <div class="hot-book-info">
                      <div class="hot-book-title">{{ book.name }}</div>
                      <div class="hot-book-meta">
                        <span class="hot-book-category">{{ book.category }}</span>
                        <span class="hot-book-count">借阅 {{ book.borrow_count }} 次</span>
                      </div>
                    </div>
                    <button @click="handleBorrow(book.bib_id)" class="quick-borrow-btn">借阅</button>
                  </div>
                </div>
              </div>

              <div class="home-section">
                <h3 class="section-title">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                    <path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/>
                  </svg>
                  最近借阅
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

          <!-- 图书检索 -->
          <div v-if="activeTab === 'search'" class="tab-content">
            <div class="search-container">
              <div class="search-header">
                <h2>图书检索</h2>
                <p>输入关键词实时搜索您感兴趣的图书</p>
              </div>
              
              <div class="search-box">
                <input 
                  v-model="searchQuery" 
                  type="text" 
                  placeholder="请输入图书名称、分类或关键词，实时搜索..."
                  class="search-input"
                />
                <button @click="handleSearch" class="search-button" :disabled="isSearching">
                  <svg v-if="!isSearching" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                  </svg>
                  <div v-else class="search-loading"></div>
                  {{ isSearching ? '搜索中...' : '搜索' }}
                </button>
              </div>

              <div v-if="searchResults.length > 0" class="search-results">
                <div class="results-header">
                  <span>找到 {{ searchResults.length }} 条结果</span>
                  <span class="search-hint">（实时搜索，输入更多内容可获得更精确的结果）</span>
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
                      <span class="result-count">借阅 {{ book.borrow_count }} 次</span>
                    </div>
                    <button @click="handleBorrow(book.bib_id)" class="result-borrow-btn">立即借阅</button>
                  </div>
                </div>
              </div>

              <div v-else-if="searchQuery && !isSearching" class="search-empty">
                <svg viewBox="0 0 24 24" fill="currentColor" width="64" height="64" class="empty-icon">
                  <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                </svg>
                <p>未找到相关图书</p>
                <p class="empty-hint">请尝试其他关键词</p>
              </div>
            </div>
          </div>

          <!-- 热门图书 -->
          <div v-if="activeTab === 'hot'" class="tab-content">
            <div class="hot-container">
              <div class="hot-header">
                <h2>热门图书排行</h2>
                <p>最受欢迎的图书，快来借阅吧</p>
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
                        <span class="hot-stat-label">借阅次数</span>
                      </div>
                    </div>
                    <button @click="handleBorrow(book.bib_id)" class="hot-borrow-btn">
                      <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                        <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                      </svg>
                      借阅
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 我的借阅 -->
          <div v-if="activeTab === 'mybooks'" class="tab-content">
            <div class="mybooks-container">
              <div class="mybooks-header">
                <h2>我的借阅记录</h2>
                <p>查看和管理您的借阅历史</p>
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
                      <span class="mybook-action" :class="record.action === 'CKO' ? 'borrow' : 'return'">{{ record.action === 'CKO' ? '借出' : '归还' }}</span>
                    </div>
                  </div>
                  <div class="mybook-date">
                    <div class="mybook-date-value">{{ record.date }}</div>
                    <div class="mybook-time">{{ record.time }}</div>
                  </div>
                </div>
              </div>

              <div v-else class="mybooks-empty">
                <svg viewBox="0 0 24 24" fill="currentColor" width="80" height="80" class="empty-icon">
                  <path d="M18 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 4h5v8l-2.5-1.5L6 12V4z"/>
                </svg>
                <h3>暂无借阅记录</h3>
                <p>快去借阅您感兴趣的图书吧</p>
                <button @click="activeTab = 'search'" class="go-search-btn">
                  <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
                    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/>
                  </svg>
                  去借书
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
  position: relative;
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
  cursor: pointer;
  transition: all 0.2s ease;
}

.avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
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
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.user-details:hover {
  opacity: 0.8;
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

.user-role-badge.user {
  color: #10b981;
  background: #ecfdf5;
}

/* 下拉菜单样式 */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 260px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
  overflow: hidden;
  z-index: 1000;
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
}

.dropdown-avatar {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dropdown-avatar span {
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.dropdown-user-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.dropdown-username {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dropdown-role {
  font-size: 12px;
  color: #64748b;
}

.dropdown-divider {
  height: 1px;
  background: #e2e8f0;
}

.dropdown-body {
  padding: 8px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.15s ease;
  color: #475569;
  font-size: 14px;
}

.dropdown-item:hover {
  background: #f8fafc;
  color: #6366f1;
}

.dropdown-item:active {
  background: #f1f5f9;
}

.dropdown-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.dropdown-footer {
  padding: 8px 0;
}

.logout-item {
  color: #ef4444;
}

.logout-item:hover {
  background: #fef2f2;
  color: #dc2626;
}

/* 下拉菜单过渡动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
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
  width: 240px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(226, 232, 240, 0.6);
  position: fixed;
  top: 70px;
  bottom: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  z-index: 50;
}

.nav-menu {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  color: #64748b;
  text-decoration: none;
}

.nav-item:hover {
  background: rgba(99, 102, 241, 0.06);
  color: #6366f1;
}

.nav-item.active {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  color: #6366f1;
  font-weight: 600;
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
  font-size: 14px;
  font-weight: 500;
}

.nav-indicator {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: linear-gradient(180deg, #6366f1, #8b5cf6);
  border-radius: 2px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(226, 232, 240, 0.6);
  text-align: center;
}

.version-badge {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  padding: 24px 32px;
  min-height: calc(100vh - 70px);
}

.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  gap: 16px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #e2e8f0;
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: #64748b;
  font-size: 14px;
}

.content-area {
  max-width: 1200px;
  margin: 0 auto;
}

.tab-content {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.welcome-banner {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 16px;
  padding: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

.welcome-text h1 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.welcome-text p {
  margin: 0;
  opacity: 0.9;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-card.primary .stat-icon {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.stat-card.success .stat-icon {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.stat-card.warning .stat-icon {
  background: rgba(245, 158, 11, 0.1);
  color: #f59e0b;
}

.stat-card.info .stat-icon {
  background: rgba(59, 130, 246, 0.1);
  color: #3b82f6;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
}

.stat-label {
  font-size: 0.85rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.home-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.home-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1rem 0;
  color: #1e293b;
  font-size: 1rem;
}

.hot-books-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.hot-book-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 10px;
  transition: background 0.2s;
}

.hot-book-item:hover {
  background: #f1f5f9;
}

.hot-rank {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  font-weight: 600;
  background: #e2e8f0;
  color: #64748b;
  flex-shrink: 0;
}

.hot-rank.top3 {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}

.hot-book-info {
  flex: 1;
  min-width: 0;
}

.hot-book-title {
  font-weight: 500;
  color: #1e293b;
  font-size: 0.9rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-book-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.25rem;
}

.quick-borrow-btn {
  padding: 0.35rem 0.75rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  transition: background 0.2s;
  flex-shrink: 0;
}

.quick-borrow-btn:hover {
  background: #4f46e5;
}

.recent-borrows-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.recent-borrow-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 0.85rem;
}

.recent-borrow-date {
  color: #94a3b8;
  font-size: 0.8rem;
  flex-shrink: 0;
  width: 80px;
}

.recent-borrow-info {
  display: flex;
  gap: 0.75rem;
  flex: 1;
}

.recent-borrow-action {
  color: #6366f1;
  font-weight: 500;
}

.recent-borrow-degree {
  color: #64748b;
}

.search-container, .hot-container, .mybooks-container {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.search-header, .hot-header, .mybooks-header {
  text-align: center;
  margin-bottom: 2rem;
}

.search-header h2, .hot-header h2, .mybooks-header h2 {
  margin: 0 0 0.5rem 0;
  color: #1e293b;
}

.search-header p, .hot-header p, .mybooks-header p {
  margin: 0;
  color: #64748b;
}

.search-box {
  display: flex;
  gap: 1rem;
  max-width: 700px;
  margin: 0 auto 2rem;
}

.search-input {
  flex: 1;
  padding: 0.875rem 1.25rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #6366f1;
}

.search-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: 500;
  transition: background 0.2s;
}

.search-button:hover:not(:disabled) {
  background: #4f46e5;
}

.search-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  padding: 0.75rem 0;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1rem;
  color: #64748b;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.search-hint {
  font-size: 0.8rem;
  color: #94a3b8;
  font-style: italic;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.result-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 1.25rem;
  transition: background 0.2s;
}

.result-card:hover {
  background: #f1f5f9;
}

.result-card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.result-icon {
  width: 40px;
  height: 40px;
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.result-title {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.95rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-card-body {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #64748b;
}

.result-borrow-btn {
  width: 100%;
  padding: 0.6rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.result-borrow-btn:hover {
  background: #4f46e5;
}

.search-empty {
  text-align: center;
  padding: 3rem 0;
  color: #94a3b8;
}

.empty-icon {
  color: #e2e8f0;
  margin-bottom: 1rem;
}

.empty-hint {
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

.hot-books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 1rem;
}

.hot-book-card {
  background: #f8fafc;
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  gap: 1rem;
  transition: background 0.2s;
}

.hot-book-card:hover {
  background: #f1f5f9;
}

.hot-card-rank {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  background: #e2e8f0;
  color: #64748b;
  flex-shrink: 0;
}

.hot-card-rank.top3 {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
}

.hot-card-content {
  flex: 1;
  min-width: 0;
}

.hot-card-title {
  font-weight: 600;
  color: #1e293b;
  font-size: 0.95rem;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-card-meta {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.hot-card-stats {
  margin-bottom: 0.75rem;
}

.hot-stat {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
}

.hot-stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #6366f1;
}

.hot-stat-label {
  font-size: 0.75rem;
  color: #94a3b8;
}

.hot-borrow-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  width: 100%;
  padding: 0.5rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: background 0.2s;
}

.hot-borrow-btn:hover {
  background: #4f46e5;
}

.mybooks-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.mybook-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.25rem;
  background: #f8fafc;
  border-radius: 10px;
  transition: background 0.2s;
}

.mybook-item:hover {
  background: #f1f5f9;
}

.mybook-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.mybook-icon.borrow {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.mybook-icon.return {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.mybook-info {
  flex: 1;
  min-width: 0;
}

.mybook-title {
  font-weight: 500;
  color: #1e293b;
  margin-bottom: 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mybook-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.mybook-category {
  font-size: 0.85rem;
  color: #64748b;
}

.mybook-action {
  font-size: 0.8rem;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.mybook-action.borrow {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
}

.mybook-action.return {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.mybook-date {
  text-align: right;
  flex-shrink: 0;
}

.mybook-date-value {
  font-size: 0.9rem;
  color: #1e293b;
  font-weight: 500;
}

.mybook-time {
  font-size: 0.8rem;
  color: #94a3b8;
}

.mybooks-empty {
  text-align: center;
  padding: 3rem 0;
  color: #94a3b8;
}

.mybooks-empty h3 {
  color: #64748b;
  margin: 1rem 0 0.5rem;
}

.mybooks-empty p {
  margin: 0 0 1.5rem;
}

.go-search-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #6366f1;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.go-search-btn:hover {
  background: #4f46e5;
}

@media (max-width: 768px) {
  .home-grid {
    grid-template-columns: 1fr;
  }
  
  .search-box {
    flex-direction: column;
  }
  
  .stats-overview {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
