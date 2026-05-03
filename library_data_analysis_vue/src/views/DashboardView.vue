<script setup>
import { ref, onMounted, onUnmounted, reactive, computed, watch, nextTick, defineAsyncComponent, shallowRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDataStore } from '@/stores/data'
import { useAuth } from '@/composables/useAuth'
import { useTime } from '@/composables/useTime'
import { useDropdown } from '@/composables/useDropdown'
import { getCache, setCache } from '@/utils/cache'
import OverviewView from './OverviewView.vue'
import CategoryView from './CategoryView.vue'
import BorrowView from './BorrowView.vue'
import ReaderView from './ReaderView.vue'
import TrendView from './TrendView.vue'
import BookView from './BookView.vue'
import PredictView from './PredictView.vue'
import ReportView from './ReportView.vue'
import SettingsView from './SettingsView.vue'

const { t } = useI18n()
const store = useDataStore()
const { username, role, checkAuth, logout } = useAuth()
const { currentTime } = useTime()
const { showDropdown: showUserDropdown, dropdownRef: userMenuRef, toggleDropdown: toggleUserDropdown } = useDropdown()

const userDropdownPos = reactive({ top: 0, right: 0 })
const settingsActiveMenu = ref('profile')

const sidebarCollapsed = ref(false)
const activeNavId = ref('overview')
const contextMenuVisible = ref(false)
const contextMenuPos = reactive({ x: 0, y: 0 })
const contextMenuTarget = ref(null)
const dragState = reactive({ dragging: false, dragIndex: -1, dropIndex: -1 })

const navItems = ref([
  { id: 'overview', i18nKey: 'nav.overview', icon: 'grid', pinned: true, closable: false, loaded: false },
  { id: 'category', i18nKey: 'nav.category', icon: 'book', pinned: false, closable: true, loaded: false },
  { id: 'borrow', i18nKey: 'nav.borrow', icon: 'book-open', pinned: false, closable: true, loaded: false },
  { id: 'reader', i18nKey: 'nav.reader', icon: 'users', pinned: false, closable: true, loaded: false },
  { id: 'trend', i18nKey: 'nav.trend', icon: 'trending-up', pinned: false, closable: true, loaded: false },
  { id: 'book', i18nKey: 'nav.book', icon: 'book-plus', pinned: false, closable: true, loaded: false },
  { id: 'predict', i18nKey: 'nav.predict', icon: 'clock', pinned: false, closable: true, loaded: false },
  { id: 'report', i18nKey: 'nav.report', icon: 'file-text', pinned: false, closable: true, loaded: false }
])

const visibleItems = computed(() => navItems.value)

const tabScrollPositions = reactive({})
const tabTransitionName = ref('slide-left')

const saveTabState = () => {
  setCache('sidebar_active_tab', activeNavId.value)
  setCache('sidebar_nav_order', navItems.value.map(n => n.id))
  setCache('sidebar_nav_pinned', navItems.value.filter(n => n.pinned).map(n => n.id))
}

const restoreTabState = () => {
  const savedActive = getCache('sidebar_active_tab')
  const savedOrder = getCache('sidebar_nav_order')
  const savedPinned = getCache('sidebar_nav_pinned')

  if (savedOrder && Array.isArray(savedOrder)) {
    const ordered = []
    const itemMap = {}
    navItems.value.forEach(item => { itemMap[item.id] = item })

    savedOrder.forEach(id => {
      if (itemMap[id]) ordered.push(itemMap[id])
    })
    navItems.value.forEach(item => {
      if (!savedOrder.includes(item.id)) ordered.push(item)
    })
    navItems.value = ordered
  }

  if (savedPinned && Array.isArray(savedPinned)) {
    navItems.value.forEach(item => {
      item.pinned = savedPinned.includes(item.id) || !item.closable
    })
  }

  if (savedActive && navItems.value.find(n => n.id === savedActive)) {
    activeNavId.value = savedActive
  }
}

const previousTabId = ref('overview')

const switchTab = (id) => {
  if (activeNavId.value === id) return
  const mainEl = document.querySelector('.main-content')
  if (mainEl) {
    tabScrollPositions[activeNavId.value] = mainEl.scrollTop
  }
  const oldIndex = navItems.value.findIndex(n => n.id === activeNavId.value)
  const newIndex = navItems.value.findIndex(n => n.id === id)
  tabTransitionName.value = newIndex > oldIndex ? 'slide-left' : 'slide-right'
  previousTabId.value = activeNavId.value
  activeNavId.value = id
  saveTabState()
  const item = navItems.value.find(n => n.id === id)
  if (item && !item.loaded) item.loaded = true
  nextTick(() => {
    const mainEl = document.querySelector('.main-content')
    if (mainEl) mainEl.scrollTop = 0
  })
}

const handleToggleUserMenu = () => {
  toggleUserDropdown()
  if (!showUserDropdown.value) return
  nextTick(() => {
    if (userMenuRef.value) {
      const rect = userMenuRef.value.getBoundingClientRect()
      userDropdownPos.top = rect.bottom + 8
      userDropdownPos.right = window.innerWidth - rect.right
    }
  })
}

const closeTab = (id) => {
  const item = navItems.value.find(n => n.id === id)
  if (!item || !item.closable || item.pinned) return
  const idx = navItems.value.findIndex(n => n.id === id)
  navItems.value.splice(idx, 1)
  if (activeNavId.value === id) {
    const nextIdx = Math.min(idx, navItems.value.length - 1)
    activeNavId.value = navItems.value[nextIdx]?.id || 'overview'
  }
  saveTabState()
}

const closeOtherTabs = (id) => {
  navItems.value = navItems.value.filter(n => n.id === id || !n.closable || n.pinned)
  if (!navItems.value.find(n => n.id === activeNavId.value)) {
    activeNavId.value = id
  }
  saveTabState()
}

const pinTab = (id) => {
  const item = navItems.value.find(n => n.id === id)
  if (item) {
    item.pinned = !item.pinned
    saveTabState()
  }
}

const showContextMenu = (e, id) => {
  e.preventDefault()
  contextMenuTarget.value = id
  contextMenuPos.x = e.clientX
  contextMenuPos.y = e.clientY
  contextMenuVisible.value = true
}

const hideContextMenu = () => {
  contextMenuVisible.value = false
  contextMenuTarget.value = null
}

const onDragStart = (e, index) => {
  dragState.dragging = true
  dragState.dragIndex = index
  e.dataTransfer.effectAllowed = 'move'
  e.target.closest('.nav-item')?.classList.add('dragging')
}

const onDragOver = (e, index) => {
  e.preventDefault()
  e.dataTransfer.dropEffect = 'move'
  dragState.dropIndex = index
}

const onDragEnd = (e) => {
  dragState.dragging = false
  if (dragState.dragIndex !== -1 && dragState.dropIndex !== -1 && dragState.dragIndex !== dragState.dropIndex) {
    const item = navItems.value.splice(dragState.dragIndex, 1)[0]
    navItems.value.splice(dragState.dropIndex, 0, item)
    saveTabState()
  }
  dragState.dragIndex = -1
  dragState.dropIndex = -1
  document.querySelectorAll('.nav-item.dragging').forEach(el => el.classList.remove('dragging'))
}

const getNavIcon = (icon) => {
  const icons = {
    grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    'book-open': '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
    users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    'trending-up': '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    'book-plus': '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><line x1="12" y1="6" x2="12" y2="12"/><line x1="9" y1="9" x2="15" y2="9"/>',
    clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    'file-text': '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>',
    'bar-chart': '<line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/>',
    upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>'
  }
  return icons[icon] || icons.grid
}

onMounted(async () => {
  if (!checkAuth()) return
  restoreTabState()
  const activeItem = navItems.value.find(n => n.id === activeNavId.value)
  if (activeItem) activeItem.loaded = true
  await store.preloadAll()
  document.addEventListener('click', hideContextMenu)
  const savedSidebar = localStorage.getItem('sidebar_collapsed')
  if (savedSidebar === 'true') sidebarCollapsed.value = true
  window.addEventListener('appearance-change', handleAppearanceChange)
})

onUnmounted(() => {
  document.removeEventListener('click', hideContextMenu)
  window.removeEventListener('appearance-change', handleAppearanceChange)
})

const handleAppearanceChange = (e) => {
  if (e.detail?.sidebarStyle) {
    sidebarCollapsed.value = e.detail.sidebarStyle === 'collapsed'
  }
}

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="dashboard" @click="hideContextMenu">
    <header class="header">
      <div class="header-left">
        <button class="sidebar-toggle btn-icon btn-secondary" @click="toggleSidebar()" :class="{ collapsed: sidebarCollapsed }">
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
            <h1>{{ t('common.systemTitle') }}</h1>
            <span class="subtitle">LIBRARY DATA ANALYTICS</span>
          </div>
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
          <button class="icon-btn btn-icon btn-secondary" :title="t('common.fullscreen')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="15 3 21 3 21 9"/>
              <polyline points="9 21 3 21 3 15"/>
              <line x1="21" y1="3" x2="14" y2="10"/>
              <line x1="3" y1="21" x2="10" y2="14"/>
            </svg>
          </button>
          <button class="icon-btn btn-icon btn-secondary" :title="t('common.notification')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
          </button>
        </div>

        <div class="user-menu" ref="userMenuRef" @click="handleToggleUserMenu">
          <div class="avatar">
            <span class="avatar-text">{{ username.charAt(0).toUpperCase() }}</span>
          </div>
          <div class="user-details">
            <span class="user-name">{{ username }}</span>
            <span class="user-role-badge" :class="role">{{ role === 'admin' ? t('common.admin') : t('common.user') }}</span>
          </div>
          <svg class="dropdown-arrow" :class="{ open: showUserDropdown }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>

        <Teleport to="body">
          <transition name="dropdown-fade">
            <div v-if="showUserDropdown" class="user-dropdown-overlay" @click="showUserDropdown = false">
              <div class="user-dropdown" :style="{ top: userDropdownPos.top + 'px', right: userDropdownPos.right + 'px' }" @click.stop>
                <div class="dropdown-header">
                  <div class="dropdown-avatar"><span>{{ username.charAt(0).toUpperCase() }}</span></div>
                  <div class="dropdown-user-info">
                    <div class="dropdown-username">{{ username }}</div>
                    <div class="dropdown-role">{{ role === 'admin' ? t('common.admin') : t('common.user') }}</div>
                  </div>
                </div>
                <div class="dropdown-divider"></div>
                <div class="dropdown-body">
                  <div class="dropdown-item" @click="switchTab('settings'); settingsActiveMenu = 'language'; showUserDropdown = false">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
                      <circle cx="12" cy="12" r="3"/>
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                    </svg>
                    <span>{{ t('common.settingsTitle') }}</span>
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
            </div>
          </transition>
        </Teleport>
      </div>
    </header>
    
    <div class="layout">
      <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
        <nav class="nav-menu">
          <div
            v-for="(item, index) in visibleItems"
            :key="item.id"
            class="nav-item"
            :class="{
              active: activeNavId === item.id,
              'drag-over': dragState.dropIndex === index,
              pinned: item.pinned
            }"
            draggable="true"
            @click="switchTab(item.id)"
            @contextmenu="showContextMenu($event, item.id)"
            @dragstart="onDragStart($event, index)"
            @dragover="onDragOver($event, index)"
            @dragend="onDragEnd"
          >
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="getNavIcon(item.icon)"/>
            </div>
            <span class="nav-label" :class="{ hidden: sidebarCollapsed }">{{ t(item.i18nKey) }}</span>
            <span v-if="item.pinned && sidebarCollapsed" class="pin-indicator"></span>
            <button
              v-if="item.closable && !item.pinned && !sidebarCollapsed"
              class="nav-close-btn btn-icon btn-ghost"
              @click.stop="closeTab(item.id)"
              :title="t('common.close')"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
                <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </nav>
        
        <div class="sidebar-footer" :class="{ hidden: sidebarCollapsed }">
          <div class="version-badge">v1.0.0</div>
        </div>
      </aside>
      
      <main class="main-content" :class="{ expanded: sidebarCollapsed }">
        <div v-if="!store.loaded" class="loading-overlay">
          <div class="loading-spinner"></div>
          <span class="loading-text">{{ t('common.loading') }}</span>
        </div>
        <template v-else>
          <transition :name="tabTransitionName" mode="out-in">
            <div v-if="activeNavId === 'overview'" key="overview" class="tab-panel">
              <OverviewView :all-data="store" @navigate="switchTab" />
            </div>
            <div v-else-if="activeNavId === 'category'" key="category" class="tab-panel">
              <CategoryView :all-data="store" />
            </div>
            <div v-else-if="activeNavId === 'borrow'" key="borrow" class="tab-panel">
              <BorrowView :all-data="store" />
            </div>
            <div v-else-if="activeNavId === 'reader'" key="reader" class="tab-panel">
              <ReaderView :all-data="store" />
            </div>
            <div v-else-if="activeNavId === 'trend'" key="trend" class="tab-panel">
              <TrendView :all-data="store" />
            </div>
            <div v-else-if="activeNavId === 'book'" key="book" class="tab-panel">
              <BookView :all-data="store" />
            </div>
            <div v-else-if="activeNavId === 'predict'" key="predict" class="tab-panel">
              <PredictView :all-data="store" />
            </div>
            <div v-else-if="activeNavId === 'report'" key="report" class="tab-panel">
              <ReportView :all-data="store" />
            </div>
            <div v-else-if="activeNavId === 'settings'" key="settings" class="tab-panel">
              <SettingsView :embedded="true" v-model:activeMenu="settingsActiveMenu" />
            </div>
          </transition>
        </template>
      </main>
    </div>

    <!-- Context Menu -->
    <transition name="context-menu">
      <div
        v-if="contextMenuVisible"
        class="context-menu"
        :style="{ left: contextMenuPos.x + 'px', top: contextMenuPos.y + 'px' }"
        @click.stop
      >
        <button class="ctx-item" @click="pinTab(contextMenuTarget); hideContextMenu()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
            <path d="M12 2v8l4 2"/>
            <circle cx="12" cy="12" r="10"/>
          </svg>
          {{ navItems.find(n => n.id === contextMenuTarget)?.pinned ? t('common.unpinTab') : t('common.pinTab') }}
        </button>
        <button
          v-if="navItems.find(n => n.id === contextMenuTarget)?.closable && !navItems.find(n => n.id === contextMenuTarget)?.pinned"
          class="ctx-item"
          @click="closeTab(contextMenuTarget); hideContextMenu()"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
          {{ t('common.closeCurrent') }}
        </button>
        <button class="ctx-item" @click="closeOtherTabs(contextMenuTarget); hideContextMenu()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <line x1="9" y1="3" x2="9" y2="21"/>
          </svg>
          {{ t('common.closeOthers') }}
        </button>
      </div>
    </transition>
  </div>
</template>

<style scoped src="./DashboardView.css"></style>
