<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const role = ref('')
const currentTime = ref('')
const isLoading = ref(true)
const activeMenu = ref('profile')

const showDropdown = ref(false)
const userMenuRef = ref(null)

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

const toggleDropdown = () => {
  showDropdown.value = !showDropdown.value
}

const closeDropdown = (event) => {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target)) {
    showDropdown.value = false
  }
}

const goToLibrary = () => {
  router.push('/library')
}

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  router.push('/login')
}

onMounted(() => {
  username.value = localStorage.getItem('username') || '未知用户'
  role.value = localStorage.getItem('role') || 'user'
  settingsForm.value.nickname = username.value
  isLoading.value = false
  
  document.addEventListener('click', closeDropdown)
  updateTime()
  setInterval(updateTime, 60000)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})

const updateTime = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  currentTime.value = `${year}-${month}-${day} ${hours}:${minutes}`
}

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
  font-size: 18px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.02em;
}

.subtitle {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
  letter-spacing: 0.05em;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.datetime {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.date {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
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
  margin-top: 70px;
  min-height: calc(100vh - 70px);
}

.sidebar {
  width: 240px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(226, 232, 240, 0.6);
  padding: 24px 0;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 70px;
  bottom: 0;
  left: 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.03);
}

.nav-menu {
  flex: 1;
  padding: 0 12px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  color: #64748b;
  text-decoration: none;
}

.nav-item:hover {
  background: #f8fafc;
  color: #475569;
}

.nav-item.active {
  background: linear-gradient(135deg, #ede9fe 0%, #e0e7ff 100%);
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
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 0 2px 2px 0;
}

.sidebar-footer {
  padding: 16px 12px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

.back-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.version-badge {
  text-align: center;
  font-size: 11px;
  color: #94a3b8;
  padding: 4px 0;
}

.main-content {
  flex: 1;
  margin-left: 240px;
  padding: 32px;
  position: relative;
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
  font-size: 14px;
  color: #64748b;
}

.content-area {
  max-width: 800px;
}

.message {
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  font-size: 14px;
  font-weight: 500;
}

.message.success {
  background: #ecfdf5;
  color: #059669;
  border: 1px solid #a7f3d0;
}

.message.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.settings-panel {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.panel-header {
  margin-bottom: 32px;
}

.panel-header h1 {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px 0;
  letter-spacing: -0.02em;
}

.panel-header p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
}

.input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
  background: #ffffff;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.input:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.input.disabled {
  background: #f8fafc;
  color: #94a3b8;
  cursor: not-allowed;
}

.form-hint {
  display: block;
  font-size: 12px;
  color: #94a3b8;
  margin-top: 6px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 8px;
}

.btn-primary {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.25);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

.btn-warning {
  background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.25);
}

.btn-warning:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.35);
}

.btn-danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.25);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.security-info {
  margin-bottom: 32px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #ffffff;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid #e2e8f0;
}

.info-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #ede9fe 0%, #e0e7ff 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.info-icon svg {
  width: 24px;
  height: 24px;
  color: #6366f1;
}

.info-content h3 {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 4px 0;
}

.info-content p {
  font-size: 14px;
  color: #64748b;
  margin: 0;
}

.danger-zone {
  padding: 24px;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #fecaca;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.section-title.danger {
  color: #dc2626;
}

.danger-text {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 16px 0;
}
</style>
