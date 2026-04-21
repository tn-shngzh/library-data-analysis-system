<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useTime } from '@/composables/useTime'
import { useDropdown } from '@/composables/useDropdown'

const router = useRouter()
const { username, role, logout } = useAuth()
const { currentTime } = useTime()
const { showDropdown, dropdownRef: userMenuRef, toggleDropdown } = useDropdown()

const isLoading = ref(true)
const activeMenu = ref('profile')

const settingsForm = ref({
  nickname: '',
  email: '',
  phone: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const message = ref({ type: '', text: '' })

const menuItems = [
  { id: 'profile', label: '个人信息', icon: 'user' },
  { id: 'password', label: '修改密码', icon: 'lock' },
  { id: 'security', label: '安全设置', icon: 'shield' }
]

const goToLibrary = () => {
  router.push('/library')
}

onMounted(() => {
  settingsForm.value.nickname = username.value
  isLoading.value = false
})

const showMessage = (type, text) => {
  message.value = { type, text }
  setTimeout(() => {
    message.value = { type: '', text: '' }
  }, 3000)
}

const handleSaveProfile = () => {
  if (!settingsForm.value.nickname.trim()) {
    showMessage('error', '昵称不能为空')
    return
  }
  
  showMessage('success', '个人信息保存成功')
}

const handleChangePassword = () => {
  if (!settingsForm.value.currentPassword) {
    showMessage('error', '请输入当前密码')
    return
  }
  
  if (!settingsForm.value.newPassword) {
    showMessage('error', '请输入新密码')
    return
  }
  
  if (settingsForm.value.newPassword.length < 6) {
    showMessage('error', '新密码长度不能少于6个字符')
    return
  }
  
  if (settingsForm.value.newPassword !== settingsForm.value.confirmPassword) {
    showMessage('error', '两次输入的密码不一致')
    return
  }
  
  showMessage('success', '密码修改成功')
  settingsForm.value.currentPassword = ''
  settingsForm.value.newPassword = ''
  settingsForm.value.confirmPassword = ''
}
</script>

<template>
  <div class="settings-system">
    <header class="header">
      <div class="header-left">
        <div class="logo-wrapper">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </div>
          <div class="title-group">
            <h1>用户设置</h1>
            <span class="subtitle">User Settings</span>
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
                <div class="dropdown-item" @click="goToLibrary">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
                    <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
                  </svg>
                  <span>返回图书馆</span>
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
          <a v-for="item in menuItems" :key="item.id" 
             class="nav-item" 
             :class="{ active: activeMenu === item.id }"
             @click="activeMenu = item.id">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path v-if="item.icon === 'user'" d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle v-if="item.icon === 'user'" cx="12" cy="7" r="4"/>
                <rect v-if="item.icon === 'lock'" x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path v-if="item.icon === 'lock'" d="M7 11V7a5 5 0 0 1 10 0v4"/>
                <path v-if="item.icon === 'shield'" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <span class="nav-label">{{ item.label }}</span>
            <div class="nav-indicator" v-if="activeMenu === item.id"></div>
          </a>
        </nav>
        
        <div class="sidebar-footer">
          <button @click="goToLibrary" class="back-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/>
            </svg>
            <span>返回图书馆</span>
          </button>
          <div class="version-badge">v0.10.0</div>
        </div>
      </aside>
      
      <main class="main-content">
        <div v-if="isLoading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <span class="loading-text">正在加载数据...</span>
        </div>

        <div v-else class="content-area">
          <div v-if="message.text" class="message" :class="message.type">
            {{ message.text }}
          </div>

          <div v-if="activeMenu === 'profile'" class="settings-panel">
            <div class="panel-header">
              <h1>个人信息</h1>
              <p>管理您的基本资料</p>
            </div>

            <div class="form-group">
              <label>用户名</label>
              <input type="text" :value="username" disabled class="input disabled" />
              <span class="form-hint">用户名不可修改</span>
            </div>

            <div class="form-group">
              <label>昵称</label>
              <input 
                v-model="settingsForm.nickname" 
                type="text" 
                placeholder="请输入昵称"
                class="input"
              />
            </div>

            <div class="form-group">
              <label>邮箱</label>
              <input 
                v-model="settingsForm.email" 
                type="email" 
                placeholder="请输入邮箱地址"
                class="input"
              />
            </div>

            <div class="form-group">
              <label>手机号</label>
              <input 
                v-model="settingsForm.phone" 
                type="tel" 
                placeholder="请输入手机号码"
                class="input"
              />
            </div>

            <button @click="handleSaveProfile" class="btn btn-primary">
              保存个人信息
            </button>
          </div>

          <div v-if="activeMenu === 'password'" class="settings-panel">
            <div class="panel-header">
              <h1>修改密码</h1>
              <p>定期修改密码可以提高账户安全性</p>
            </div>

            <div class="form-group">
              <label>当前密码</label>
              <input 
                v-model="settingsForm.currentPassword" 
                type="password" 
                placeholder="请输入当前密码"
                class="input"
              />
            </div>

            <div class="form-group">
              <label>新密码</label>
              <input 
                v-model="settingsForm.newPassword" 
                type="password" 
                placeholder="请输入新密码（至少6个字符）"
                class="input"
              />
            </div>

            <div class="form-group">
              <label>确认新密码</label>
              <input 
                v-model="settingsForm.confirmPassword" 
                type="password" 
                placeholder="请再次输入新密码"
                class="input"
              />
            </div>

            <button @click="handleChangePassword" class="btn btn-warning">
              修改密码
            </button>
          </div>

          <div v-if="activeMenu === 'security'" class="settings-panel">
            <div class="panel-header">
              <h1>安全设置</h1>
              <p>管理您的账户安全选项</p>
            </div>

            <div class="security-info">
              <div class="info-item">
                <div class="info-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  </svg>
                </div>
                <div class="info-content">
                  <h3>账户安全状态</h3>
                  <p>您的账户目前处于安全状态</p>
                </div>
              </div>

              <div class="info-item">
                <div class="info-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                    <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                  </svg>
                </div>
                <div class="info-content">
                  <h3>密码强度</h3>
                  <p>建议定期修改密码，使用强密码保护账户</p>
                </div>
              </div>
            </div>

            <div class="danger-zone">
              <h2 class="section-title danger">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="22" height="22">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                  <line x1="12" y1="9" x2="12" y2="13"/>
                  <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                危险操作
              </h2>
              <p class="danger-text">以下操作不可撤销，请谨慎操作。</p>
              <button class="btn btn-danger" disabled>
                注销账户（暂未开放）
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
.settings-system {
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
  width: 24px;
  height: 24px;
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
  color: var(--color-neutral-800);
  margin: 0;
  letter-spacing: var(--tracking-tight);
}

.subtitle {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
  font-weight: var(--font-medium);
  letter-spacing: var(--tracking-wide);
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
  gap: 2px;
}

.date {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--color-neutral-500);
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

.logout-btn {
  width: 32px;
  height: 32px;
  background: transparent;
  color: var(--color-neutral-400);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-base);
}

.logout-btn svg {
  width: 18px;
  height: 18px;
}

.logout-btn:hover {
  background: var(--color-danger-50);
  color: var(--color-danger-500);
}

.layout {
  display: flex;
  margin-top: var(--header-height);
  min-height: calc(100vh - var(--header-height));
}

.sidebar {
  width: var(--sidebar-width);
  background: var(--gradient-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid var(--color-neutral-200);
  padding: var(--space-6) 0;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: var(--header-height);
  bottom: 0;
  left: 0;
  box-shadow: var(--shadow-xs);
}

.nav-menu {
  flex: 1;
  padding: 0 var(--space-3);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 12px var(--space-4);
  margin-bottom: var(--space-1);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-base);
  position: relative;
  color: var(--color-neutral-500);
  text-decoration: none;
}

.nav-item:hover {
  background: var(--color-neutral-50);
  color: var(--color-neutral-600);
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
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: var(--gradient-primary);
  border-radius: 0 2px 2px 0;
}

.sidebar-footer {
  padding: var(--space-4) var(--space-3);
  border-top: 1px solid var(--color-neutral-200);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 10px var(--space-4);
  background: var(--gradient-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  transition: all var(--transition-base);
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

.back-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-primary);
}

.version-badge {
  text-align: center;
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
  padding: var(--space-1) 0;
}

.main-content {
  flex: 1;
  margin-left: var(--sidebar-width);
  padding: var(--space-8);
  position: relative;
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

.content-area {
  max-width: 800px;
}

.message {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-6);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.message.success {
  background: var(--color-success-50);
  color: var(--color-success-600);
  border: 1px solid var(--color-success-100);
}

.message.error {
  background: var(--color-danger-50);
  color: var(--color-danger-600);
  border: 1px solid var(--color-danger-100);
}

.settings-panel {
  animation: fadeInUp 0.3s ease;
}

.panel-header {
  margin-bottom: var(--space-8);
}

.panel-header h1 {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--color-neutral-900);
  margin: 0 0 var(--space-2) 0;
  letter-spacing: var(--tracking-tight);
}

.panel-header p {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin: 0;
}

.form-group {
  margin-bottom: var(--space-6);
}

.form-group label {
  display: block;
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-700);
  margin-bottom: var(--space-2);
}

.input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-neutral-800);
  background: var(--color-neutral-0);
  transition: all var(--transition-base);
  box-sizing: border-box;
}

.input:focus {
  outline: none;
  border-color: var(--color-primary-500);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}

.input.disabled {
  background: var(--color-neutral-50);
  color: var(--color-neutral-400);
  cursor: not-allowed;
}

.form-hint {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
  margin-top: var(--space-2);
}

.btn {
  padding: var(--space-3) var(--space-6);
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  cursor: pointer;
  transition: all var(--transition-base);
  margin-top: var(--space-2);
}

.btn-primary {
  background: var(--gradient-primary);
  color: white;
  box-shadow: var(--shadow-primary);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-primary-lg);
}

.btn-warning {
  background: var(--gradient-warning);
  color: white;
  box-shadow: var(--shadow-warning);
}

.btn-warning:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35);
}

.btn-danger {
  background: var(--gradient-danger);
  color: white;
  box-shadow: var(--shadow-danger);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.security-info {
  margin-bottom: var(--space-8);
}

.info-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-3);
  border: 1px solid var(--color-neutral-200);
}

.info-icon {
  width: 48px;
  height: 48px;
  background: var(--color-primary-50);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.info-icon svg {
  width: 24px;
  height: 24px;
  color: var(--color-primary-500);
}

.info-content h3 {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-800);
  margin: 0 0 var(--space-1) 0;
}

.info-content p {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin: 0;
}

.danger-zone {
  padding: var(--space-6);
  background: var(--color-neutral-0);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-danger-100);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  margin: 0 0 var(--space-3) 0;
}

.section-title.danger {
  color: var(--color-danger-600);
}

.danger-text {
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
  margin: 0 0 var(--space-4) 0;
}

@media (max-width: 1024px) {
  .settings-grid {
    grid-template-columns: 1fr;
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

  .form-group {
    margin-bottom: var(--space-4);
  }
}
</style>
