<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import { useTime } from '@/composables/useTime'
import { useDropdown } from '@/composables/useDropdown'
import { SUPPORTED_LOCALES, setLocale } from '@/i18n'
import { clearCache } from '@/utils/cache'

const props = defineProps({
  embedded: {
    type: Boolean,
    default: false
  },
  activeMenu: {
    type: String,
    default: 'profile'
  }
})

const emit = defineEmits(['update:activeMenu'])

const { t, locale } = useI18n()
const router = useRouter()
const { username, role, checkAuth, logout } = useAuth()
const { currentTime } = useTime()
const { showDropdown, dropdownRef: userMenuRef, toggleDropdown } = useDropdown()

const localActiveMenu = ref('profile')
const activeMenuValue = computed(() => props.embedded ? props.activeMenu : localActiveMenu.value)
const setActiveMenu = (val) => {
  if (props.embedded) {
    emit('update:activeMenu', val)
  } else {
    localActiveMenu.value = val
  }
}

const message = ref({ type: '', text: '' })
const showConfirmModal = ref(false)
const confirmAction = ref(null)
const confirmMessage = ref('')

const settingsForm = ref({
  nickname: '',
  email: '',
  phone: '',
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const appearanceSettings = reactive({
  theme: 'light',
  fontSize: 'medium',
  animations: true,
  accentColor: 'blue',
  sidebarStyle: 'expanded',
  borderRadius: 'medium',
  compactMode: false,
  backgroundPattern: 'none'
})

const accentColors = computed(() => [
  { key: 'blue', value: '#3b82f6', label: t('settings.colorBlue') },
  { key: 'purple', value: '#8b5cf6', label: t('settings.colorPurple') },
  { key: 'green', value: '#10b981', label: t('settings.colorGreen') },
  { key: 'orange', value: '#f59e0b', label: t('settings.colorOrange') },
  { key: 'red', value: '#ef4444', label: t('settings.colorRed') },
  { key: 'teal', value: '#14b8a6', label: t('settings.colorTeal') }
])

const notificationSettings = reactive({
  emailNotification: true,
  borrowReminder: true,
  systemAnnouncement: true,
  dataReport: false,
  notificationSound: true
})

const privacySettings = reactive({
  profileVisibility: 'public',
  borrowHistoryVisible: false,
  dataCollection: true
})

const currentLocale = computed(() =>
  SUPPORTED_LOCALES.find(l => l.code === locale.value) || SUPPORTED_LOCALES[0]
)

const menuItems = computed(() => [
  { id: 'profile', i18nKey: 'settings.profile', icon: 'user', desc: t('settings.profileDesc') },
  { id: 'password', i18nKey: 'settings.password', icon: 'lock', desc: t('settings.passwordDesc') },
  { id: 'security', i18nKey: 'settings.security', icon: 'shield', desc: t('settings.securityDesc') },
  { id: 'appearance', i18nKey: 'settings.appearance', icon: 'palette', desc: t('settings.appearanceDesc') },
  { id: 'language', i18nKey: 'settings.language', icon: 'globe', desc: t('settings.languageDesc') },
  { id: 'notification', i18nKey: 'settings.notification', icon: 'bell', desc: t('settings.notificationDesc') },
  { id: 'privacy', i18nKey: 'settings.privacy', icon: 'eye', desc: t('settings.privacyDesc') },
  { id: 'about', i18nKey: 'settings.about', icon: 'info', desc: t('settings.aboutDesc') }
])

const goToDashboard = () => {
  router.push('/dashboard')
}

onMounted(() => {
  if (!checkAuth()) return
  settingsForm.value.nickname = username.value
  const savedAppearance = localStorage.getItem('settings_appearance')
  if (savedAppearance) {
    try { Object.assign(appearanceSettings, JSON.parse(savedAppearance)) } catch {}
  }
  applyAppearanceSettings()
  const savedNotification = localStorage.getItem('settings_notification')
  if (savedNotification) {
    try { Object.assign(notificationSettings, JSON.parse(savedNotification)) } catch {}
  }
  const savedPrivacy = localStorage.getItem('settings_privacy')
  if (savedPrivacy) {
    try { Object.assign(privacySettings, JSON.parse(savedPrivacy)) } catch {}
  }
})

const showMessage = (type, text) => {
  message.value = { type, text }
  setTimeout(() => { message.value = { type: '', text: '' } }, 3000)
}

const handleSaveProfile = () => {
  if (!settingsForm.value.nickname.trim()) {
    showMessage('error', t('settings.nicknameRequired'))
    return
  }
  showMessage('success', t('settings.profileSaved'))
}

const handleChangePassword = () => {
  if (!settingsForm.value.currentPassword) {
    showMessage('error', t('settings.currentPasswordRequired'))
    return
  }
  if (!settingsForm.value.newPassword) {
    showMessage('error', t('settings.newPasswordRequired'))
    return
  }
  if (settingsForm.value.newPassword.length < 6) {
    showMessage('error', t('settings.newPasswordTooShort'))
    return
  }
  if (settingsForm.value.newPassword !== settingsForm.value.confirmPassword) {
    showMessage('error', t('settings.passwordMismatch'))
    return
  }
  showMessage('success', t('settings.passwordChanged'))
  settingsForm.value.currentPassword = ''
  settingsForm.value.newPassword = ''
  settingsForm.value.confirmPassword = ''
}

const languageChangedMsg = ref(false)

const handleSelectLocale = async (code) => {
  await setLocale(code)
  languageChangedMsg.value = true
  setTimeout(() => {
    languageChangedMsg.value = false
  }, 3000)
}

const saveAppearanceSettings = () => {
  localStorage.setItem('settings_appearance', JSON.stringify(appearanceSettings))
  applyAppearanceSettings()
}

const accentColorMap = {
  blue: { 50: '#eef2ff', 100: '#e0e7ff', 200: '#c7d2fe', 300: '#a5b4fc', 400: '#818cf8', 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca', 800: '#3730a3', 900: '#312e81' },
  purple: { 50: '#f5f3ff', 100: '#ede9fe', 200: '#ddd6fe', 300: '#c4b5fd', 400: '#a78bfa', 500: '#8b5cf6', 600: '#7c3aed', 700: '#6d28d9', 800: '#5b21b6', 900: '#4c1d95' },
  green: { 50: '#ecfdf5', 100: '#d1fae5', 200: '#a7f3d0', 300: '#6ee7b7', 400: '#34d399', 500: '#10b981', 600: '#059669', 700: '#047857', 800: '#065f46', 900: '#064e3b' },
  orange: { 50: '#fffbeb', 100: '#fef3c7', 200: '#fde68a', 300: '#fcd34d', 400: '#fbbf24', 500: '#f59e0b', 600: '#d97706', 700: '#b45309', 800: '#92400e', 900: '#78350f' },
  red: { 50: '#fef2f2', 100: '#fee2e2', 200: '#fecaca', 300: '#fca5a5', 400: '#f87171', 500: '#ef4444', 600: '#dc2626', 700: '#b91c1c', 800: '#991b1b', 900: '#7f1d1d' },
  teal: { 50: '#f0fdfa', 100: '#ccfbf1', 200: '#99f6e4', 300: '#5eead4', 400: '#2dd4bf', 500: '#14b8a6', 600: '#0d9488', 700: '#0f766e', 800: '#115e59', 900: '#134e4a' }
}

const applyAppearanceSettings = () => {
  const root = document.documentElement

  if (appearanceSettings.theme === 'dark') {
    root.setAttribute('data-theme', 'dark')
  } else if (appearanceSettings.theme === 'auto') {
    root.removeAttribute('data-theme')
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      root.setAttribute('data-theme', 'dark')
    }
  } else {
    root.removeAttribute('data-theme')
  }

  const colors = accentColorMap[appearanceSettings.accentColor] || accentColorMap.blue
  Object.entries(colors).forEach(([shade, value]) => {
    root.style.setProperty(`--color-primary-${shade}`, value)
  })
  root.style.setProperty('--gradient-primary', `linear-gradient(135deg, ${colors[500]} 0%, ${colors[400]} 100%)`)
  root.style.setProperty('--gradient-primary-hover', `linear-gradient(135deg, ${colors[600]} 0%, ${colors[500]} 100%)`)
  root.style.setProperty('--shadow-primary', `0 4px 14px ${colors[500]}40`)
  root.style.setProperty('--shadow-primary-lg', `0 8px 24px ${colors[500]}4d`)
  root.style.setProperty('--shadow-glow', `0 0 20px ${colors[500]}26`)

  const fontScale = { small: 0.875, medium: 1, large: 1.125 }
  root.style.setProperty('--font-scale', fontScale[appearanceSettings.fontSize] || 1)

  const radiusMap = { small: { sm: '3px', md: '4px', lg: '6px', xl: '8px', '2xl': '10px' }, medium: { sm: '6px', md: '8px', lg: '12px', xl: '16px', '2xl': '20px' }, large: { sm: '10px', md: '14px', lg: '18px', xl: '22px', '2xl': '26px' } }
  const radii = radiusMap[appearanceSettings.borderRadius] || radiusMap.medium
  Object.entries(radii).forEach(([key, val]) => {
    root.style.setProperty(`--radius-${key}`, val)
  })

  if (appearanceSettings.compactMode) {
    root.classList.add('compact-mode')
  } else {
    root.classList.remove('compact-mode')
  }

  if (!appearanceSettings.animations) {
    root.classList.add('reduce-motion')
  } else {
    root.classList.remove('reduce-motion')
  }

  root.classList.remove('bg-none', 'bg-dots', 'bg-grid', 'bg-stripes')
  root.classList.add(`bg-${appearanceSettings.backgroundPattern}`)

  localStorage.setItem('sidebar_collapsed', appearanceSettings.sidebarStyle === 'collapsed' ? 'true' : 'false')
  window.dispatchEvent(new CustomEvent('appearance-change', { detail: { sidebarStyle: appearanceSettings.sidebarStyle } }))
}

const saveNotificationSettings = () => {
  localStorage.setItem('settings_notification', JSON.stringify(notificationSettings))
  showMessage('success', t('settings.profileSaved'))
}

const savePrivacySettings = () => {
  localStorage.setItem('settings_privacy', JSON.stringify(privacySettings))
  showMessage('success', t('settings.profileSaved'))
}

const handleClearCache = () => {
  confirmMessage.value = t('settings.clearCacheDesc')
  confirmAction.value = () => {
    clearCache()
    showMessage('success', t('settings.cacheCleared'))
  }
  showConfirmModal.value = true
}

const handleConfirm = () => {
  if (confirmAction.value) confirmAction.value()
  showConfirmModal.value = false
  confirmAction.value = null
}

const handleCancelConfirm = () => {
  showConfirmModal.value = false
  confirmAction.value = null
}

const getNavIcon = (icon) => {
  const icons = {
    user: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    lock: '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    palette: '<circle cx="13.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="10.5" r="2.5"/><circle cx="8.5" cy="7.5" r="2.5"/><circle cx="6.5" cy="12.5" r="2.5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.5-.67 1.5-1.5 0-.39-.15-.74-.39-1.04-.23-.29-.38-.63-.38-1.04 0-.93.76-1.69 1.69-1.69H16c3.31 0 6-2.69 6-6 0-5.5-4.5-9.83-10-9.83z"/>',
    globe: '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    bell: '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
    eye: '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    info: '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>'
  }
  return icons[icon] || icons.info
}
</script>
<template>
  <div v-if="embedded" class="settings-embedded">
    <div v-if="message.text" class="message-toast" :class="message.type">
      <svg v-if="message.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
      {{ message.text }}
    </div>
    <transition name="fade" mode="out-in">
      <div :key="activeMenuValue" class="content-area">
        <div v-if="activeMenuValue === 'profile'" class="settings-panel">
          <div class="panel-header"><h1>{{ t('settings.profile') }}</h1><p>{{ t('settings.profileDesc') }}</p></div>
          <div class="avatar-section">
            <div class="avatar-large"><span>{{ username.charAt(0).toUpperCase() }}</span></div>
            <div class="avatar-info"><div class="avatar-name">{{ username }}</div><div class="avatar-role">{{ role === 'admin' ? t('common.admin') : t('common.user') }}</div></div>
          </div>
          <div class="form-section">
            <div class="form-group"><label>{{ t('settings.username') }}</label><input type="text" :value="username" disabled class="input disabled" /><span class="form-hint">{{ t('settings.usernameHint') }}</span></div>
            <div class="form-group"><label>{{ t('settings.nickname') }}</label><input v-model="settingsForm.nickname" type="text" :placeholder="t('settings.nicknamePlaceholder')" class="input" /></div>
            <div class="form-group"><label>{{ t('settings.email') }}</label><input v-model="settingsForm.email" type="email" :placeholder="t('settings.emailPlaceholder')" class="input" /></div>
            <div class="form-group"><label>{{ t('settings.phone') }}</label><input v-model="settingsForm.phone" type="tel" :placeholder="t('settings.phonePlaceholder')" class="input" /></div>
          </div>
          <div class="form-actions"><button @click="handleSaveProfile" class="btn btn-primary">{{ t('settings.saveProfile') }}</button></div>
        </div>
        <div v-if="activeMenuValue === 'password'" class="settings-panel">
          <div class="panel-header"><h1>{{ t('settings.password') }}</h1><p>{{ t('settings.passwordDesc') }}</p></div>
          <div class="form-section">
            <div class="form-group"><label>{{ t('settings.currentPassword') }}</label><input v-model="settingsForm.currentPassword" type="password" :placeholder="t('settings.currentPasswordPlaceholder')" class="input" /></div>
            <div class="form-group">
              <label>{{ t('settings.newPassword') }}</label>
              <input v-model="settingsForm.newPassword" type="password" :placeholder="t('settings.newPasswordPlaceholder')" class="input" />
              <div class="password-strength" v-if="settingsForm.newPassword">
                <div class="strength-bar"><div class="strength-fill" :class="settingsForm.newPassword.length < 4 ? 'weak' : settingsForm.newPassword.length < 8 ? 'medium' : 'strong'" :style="{ width: Math.min(settingsForm.newPassword.length / 10 * 100, 100) + '%' }"></div></div>
                <span class="strength-text" :class="settingsForm.newPassword.length < 4 ? 'weak' : settingsForm.newPassword.length < 8 ? 'medium' : 'strong'">{{ settingsForm.newPassword.length < 4 ? t('settings.weak') : settingsForm.newPassword.length < 8 ? t('settings.medium') : t('settings.strong') }}</span>
              </div>
            </div>
            <div class="form-group"><label>{{ t('settings.confirmPassword') }}</label><input v-model="settingsForm.confirmPassword" type="password" :placeholder="t('settings.confirmPasswordPlaceholder')" class="input" /></div>
          </div>
          <div class="form-actions"><button @click="handleChangePassword" class="btn btn-warning">{{ t('settings.changePassword') }}</button></div>
        </div>
        <div v-if="activeMenuValue === 'security'" class="settings-panel">
          <div class="panel-header"><h1>{{ t('settings.security') }}</h1><p>{{ t('settings.securityDesc') }}</p></div>
          <div class="security-cards">
            <div class="security-card safe">
              <div class="security-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
              <div class="security-card-content"><h3>{{ t('settings.accountSecurityStatus') }}</h3><p>{{ t('settings.accountSecuritySafe') }}</p></div>
              <div class="security-badge safe">{{ t('settings.strong') }}</div>
            </div>
            <div class="security-card">
              <div class="security-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
              <div class="security-card-content"><h3>{{ t('settings.passwordStrengthTip') }}</h3></div>
            </div>
          </div>
          <div class="danger-zone">
            <h2 class="section-title danger"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>{{ t('settings.dangerZone') }}</h2>
            <p class="danger-text">{{ t('settings.dangerZoneDesc') }}</p>
            <button class="btn btn-danger" disabled>{{ t('settings.deleteAccountDisabled') }}</button>
          </div>
        </div>
        <div v-if="activeMenuValue === 'appearance'" class="settings-panel">
          <div class="panel-header"><h1>{{ t('settings.appearance') }}</h1><p>{{ t('settings.appearanceDesc') }}</p></div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.theme') }}</h3>
            <div class="option-cards">
              <div class="option-card" :class="{ active: appearanceSettings.theme === 'light' }" @click="appearanceSettings.theme = 'light'; saveAppearanceSettings()">
                <div class="option-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg></div>
                <span>{{ t('settings.themeLight') }}</span>
                <svg v-if="appearanceSettings.theme === 'light'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" class="check-mark"><path d="M20 6L9 17l-5-5"/></svg>
              </div>
              <div class="option-card" :class="{ active: appearanceSettings.theme === 'dark' }" @click="appearanceSettings.theme = 'dark'; saveAppearanceSettings()">
                <div class="option-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></div>
                <span>{{ t('settings.themeDark') }}</span>
                <svg v-if="appearanceSettings.theme === 'dark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" class="check-mark"><path d="M20 6L9 17l-5-5"/></svg>
              </div>
              <div class="option-card" :class="{ active: appearanceSettings.theme === 'auto' }" @click="appearanceSettings.theme = 'auto'; saveAppearanceSettings()">
                <div class="option-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg></div>
                <span>{{ t('settings.themeAuto') }}</span>
                <svg v-if="appearanceSettings.theme === 'auto'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" class="check-mark"><path d="M20 6L9 17l-5-5"/></svg>
              </div>
            </div>
          </div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.accentColor') }}</h3>
            <div class="accent-color-list">
              <div
                v-for="color in accentColors"
                :key="color.key"
                class="accent-color-item"
                :class="{ active: appearanceSettings.accentColor === color.key }"
                @click="appearanceSettings.accentColor = color.key; saveAppearanceSettings()"
              >
                <div class="accent-color-dot" :style="{ background: color.value }"></div>
                <span>{{ color.label }}</span>
                <svg v-if="appearanceSettings.accentColor === color.key" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="14" height="14" class="accent-check"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
            </div>
          </div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.fontSize') }}</h3>
            <div class="option-cards compact">
              <div class="option-card compact" :class="{ active: appearanceSettings.fontSize === 'small' }" @click="appearanceSettings.fontSize = 'small'; saveAppearanceSettings()">
                <span class="font-preview small">Aa</span><span>{{ t('settings.fontSizeSmall') }}</span>
              </div>
              <div class="option-card compact" :class="{ active: appearanceSettings.fontSize === 'medium' }" @click="appearanceSettings.fontSize = 'medium'; saveAppearanceSettings()">
                <span class="font-preview medium">Aa</span><span>{{ t('settings.fontSizeMedium') }}</span>
              </div>
              <div class="option-card compact" :class="{ active: appearanceSettings.fontSize === 'large' }" @click="appearanceSettings.fontSize = 'large'; saveAppearanceSettings()">
                <span class="font-preview large">Aa</span><span>{{ t('settings.fontSizeLarge') }}</span>
              </div>
            </div>
          </div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.borderRadius') }}</h3>
            <div class="option-cards compact">
              <div class="option-card compact" :class="{ active: appearanceSettings.borderRadius === 'small' }" @click="appearanceSettings.borderRadius = 'small'; saveAppearanceSettings()">
                <span class="radius-preview small-r"></span><span>{{ t('settings.borderRadiusSmall') }}</span>
              </div>
              <div class="option-card compact" :class="{ active: appearanceSettings.borderRadius === 'medium' }" @click="appearanceSettings.borderRadius = 'medium'; saveAppearanceSettings()">
                <span class="radius-preview medium-r"></span><span>{{ t('settings.borderRadiusMedium') }}</span>
              </div>
              <div class="option-card compact" :class="{ active: appearanceSettings.borderRadius === 'large' }" @click="appearanceSettings.borderRadius = 'large'; saveAppearanceSettings()">
                <span class="radius-preview large-r"></span><span>{{ t('settings.borderRadiusLarge') }}</span>
              </div>
            </div>
          </div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.sidebarStyle') }}</h3>
            <div class="option-cards compact">
              <div class="option-card compact" :class="{ active: appearanceSettings.sidebarStyle === 'expanded' }" @click="appearanceSettings.sidebarStyle = 'expanded'; saveAppearanceSettings()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
                <span>{{ t('settings.sidebarExpanded') }}</span>
              </div>
              <div class="option-card compact" :class="{ active: appearanceSettings.sidebarStyle === 'collapsed' }" @click="appearanceSettings.sidebarStyle = 'collapsed'; saveAppearanceSettings()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="3" width="4" height="18" rx="1"/><rect x="9" y="3" width="12" height="18" rx="2"/></svg>
                <span>{{ t('settings.sidebarCollapsed') }}</span>
              </div>
            </div>
          </div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.backgroundPattern') }}</h3>
            <div class="option-cards compact">
              <div class="option-card compact" :class="{ active: appearanceSettings.backgroundPattern === 'none' }" @click="appearanceSettings.backgroundPattern = 'none'; saveAppearanceSettings()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="3" x2="21" y2="21"/></svg>
                <span>{{ t('settings.patternNone') }}</span>
              </div>
              <div class="option-card compact" :class="{ active: appearanceSettings.backgroundPattern === 'dots' }" @click="appearanceSettings.backgroundPattern = 'dots'; saveAppearanceSettings()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="7" cy="7" r="1.5"/><circle cx="17" cy="7" r="1.5"/><circle cx="7" cy="17" r="1.5"/><circle cx="17" cy="17" r="1.5"/><circle cx="12" cy="12" r="1.5"/></svg>
                <span>{{ t('settings.patternDots') }}</span>
              </div>
              <div class="option-card compact" :class="{ active: appearanceSettings.backgroundPattern === 'grid' }" @click="appearanceSettings.backgroundPattern = 'grid'; saveAppearanceSettings()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
                <span>{{ t('settings.patternGrid') }}</span>
              </div>
              <div class="option-card compact" :class="{ active: appearanceSettings.backgroundPattern === 'stripes' }" @click="appearanceSettings.backgroundPattern = 'stripes'; saveAppearanceSettings()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><line x1="0" y1="6" x2="24" y2="6"/><line x1="0" y1="12" x2="24" y2="12"/><line x1="0" y1="18" x2="24" y2="18"/></svg>
                <span>{{ t('settings.patternStripes') }}</span>
              </div>
            </div>
          </div>
          <div class="settings-group">
            <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.animation') }}</h3><p>{{ appearanceSettings.animations ? t('settings.animationEnabled') : t('settings.animationDisabled') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="appearanceSettings.animations" @change="saveAppearanceSettings" /><span class="toggle-slider"></span></label></div>
            <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.compactMode') }}</h3><p>{{ t('settings.compactModeDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="appearanceSettings.compactMode" @change="saveAppearanceSettings" /><span class="toggle-slider"></span></label></div>
          </div>
        </div>
        <div v-if="activeMenuValue === 'language'" class="settings-panel">
          <div class="panel-header"><h1>{{ t('settings.language') }}</h1><p>{{ t('settings.languageDesc') }}</p></div>
          <div class="settings-group">
            <div class="lang-current-banner">
              <div class="lang-current-left">
                <span class="lang-current-flag">{{ currentLocale.flag }}</span>
                <div class="lang-current-info">
                  <span class="lang-current-name">{{ currentLocale.name }}</span>
                  <span class="lang-current-native">{{ currentLocale.nativeName }}</span>
                </div>
              </div>
              <div class="lang-current-badge">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="20 6 9 17 4 12"/></svg>
                {{ t('settings.currentLanguage') }}
              </div>
            </div>
          </div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.selectLanguage') }}</h3>
            <div class="lang-list">
              <div
                v-for="lang in SUPPORTED_LOCALES"
                :key="lang.code"
                class="lang-item"
                :class="{ active: locale === lang.code }"
                @click="handleSelectLocale(lang.code)"
              >
                <span class="lang-item-flag">{{ lang.flag }}</span>
                <div class="lang-item-info">
                  <span class="lang-item-name">{{ lang.name }}</span>
                  <span class="lang-item-native">{{ lang.nativeName }}</span>
                </div>
                <div v-if="locale === lang.code" class="lang-item-check">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="18" height="18"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
                <div v-else class="lang-item-radio"></div>
              </div>
            </div>
            <transition name="lang-msg">
              <div v-if="languageChangedMsg" class="lang-changed-msg">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="20 6 9 17 4 12"/></svg>
                {{ t('settings.languageChanged') }}
              </div>
            </transition>
          </div>
          <div class="settings-group">
            <div class="lang-tip">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
              <span>{{ t('settings.languageSwitchNote') }}</span>
            </div>
          </div>
        </div>
        <div v-if="activeMenuValue === 'notification'" class="settings-panel">
          <div class="panel-header"><h1>{{ t('settings.notification') }}</h1><p>{{ t('settings.notificationDesc') }}</p></div>
          <div class="settings-group">
            <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.emailNotification') }}</h3><p>{{ t('settings.emailNotificationDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.emailNotification" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
            <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.borrowReminder') }}</h3><p>{{ t('settings.borrowReminderDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.borrowReminder" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
            <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.systemAnnouncement') }}</h3><p>{{ t('settings.systemAnnouncementDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.systemAnnouncement" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
            <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.dataReport') }}</h3><p>{{ t('settings.dataReportDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.dataReport" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
            <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.notificationSound') }}</h3><p>{{ t('settings.notificationSoundDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.notificationSound" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
          </div>
        </div>
        <div v-if="activeMenuValue === 'privacy'" class="settings-panel">
          <div class="panel-header"><h1>{{ t('settings.privacy') }}</h1><p>{{ t('settings.privacyDesc') }}</p></div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.profileVisibility') }}</h3>
            <div class="option-cards">
              <div class="option-card compact" :class="{ active: privacySettings.profileVisibility === 'public' }" @click="privacySettings.profileVisibility = 'public'; savePrivacySettings()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                <span>{{ t('settings.profilePublic') }}</span><span class="option-desc">{{ t('settings.profilePublicDesc') }}</span>
              </div>
              <div class="option-card compact" :class="{ active: privacySettings.profileVisibility === 'private' }" @click="privacySettings.profileVisibility = 'private'; savePrivacySettings()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                <span>{{ t('settings.profilePrivate') }}</span><span class="option-desc">{{ t('settings.profilePrivateDesc') }}</span>
              </div>
            </div>
          </div>
          <div class="settings-group">
            <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.borrowHistory') }}</h3><p>{{ privacySettings.borrowHistoryVisible ? t('settings.borrowHistoryVisible') : t('settings.borrowHistoryHidden') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="privacySettings.borrowHistoryVisible" @change="savePrivacySettings" /><span class="toggle-slider"></span></label></div>
            <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.dataCollection') }}</h3><p>{{ t('settings.dataCollectionDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="privacySettings.dataCollection" @change="savePrivacySettings" /><span class="toggle-slider"></span></label></div>
          </div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.clearCache') }}</h3>
            <p class="group-desc">{{ t('settings.clearCacheDesc') }}</p>
            <button class="btn btn-outline" @click="handleClearCache">{{ t('settings.clearCacheBtn') }}</button>
          </div>
          <div class="settings-group">
            <h3 class="group-title">{{ t('settings.exportData') }}</h3>
            <p class="group-desc">{{ t('settings.exportDataDesc') }}</p>
            <button class="btn btn-outline">{{ t('settings.exportDataBtn') }}</button>
          </div>
        </div>
        <div v-if="activeMenuValue === 'about'" class="settings-panel">
          <div class="panel-header"><h1>{{ t('settings.about') }}</h1><p>{{ t('settings.aboutDesc') }}</p></div>
          <div class="about-card">
            <div class="about-logo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg></div>
            <h2>{{ t('common.systemTitle') }}</h2>
            <div class="about-version">v1.0.0</div>
          </div>
          <div class="about-info-list">
            <div class="about-info-item"><span class="info-label">{{ t('settings.systemVersion') }}</span><span class="info-value">1.0.0</span></div>
            <div class="about-info-item"><span class="info-label">{{ t('settings.buildDate') }}</span><span class="info-value">2026-04-22</span></div>
            <div class="about-info-item"><span class="info-label">{{ t('settings.frontend') }}</span><span class="info-value">Vue 3 + Vite</span></div>
            <div class="about-info-item"><span class="info-label">{{ t('settings.backend') }}</span><span class="info-value">FastAPI + Python</span></div>
            <div class="about-info-item"><span class="info-label">{{ t('settings.database') }}</span><span class="info-value">PostgreSQL</span></div>
          </div>
          <div class="about-footer">
            <div class="about-links">
              <a href="#" class="about-link">{{ t('settings.openSourceLicense') }}</a>
              <a href="#" class="about-link">{{ t('settings.contactUs') }}</a>
              <a href="#" class="about-link">{{ t('settings.feedback') }}</a>
            </div>
          </div>
        </div>
      </div>
    </transition>
    <transition name="modal">
      <div v-if="showConfirmModal" class="modal-overlay" @click.self="handleCancelConfirm">
        <div class="modal-card">
          <h3>{{ t('common.confirm') || '确认' }}</h3>
          <p>{{ confirmMessage }}</p>
          <div class="modal-actions">
            <button class="btn btn-outline" @click="handleCancelConfirm">{{ t('settings.cancel') }}</button>
            <button class="btn btn-primary" @click="handleConfirm">{{ t('settings.save') }}</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
  <div v-else class="settings-page">
    <header class="header">
      <div class="header-left">
        <button class="back-btn" @click="goToDashboard">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div class="logo-wrapper">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
          </div>
          <div class="title-group">
            <h1>{{ t('settings.title') }}</h1>
            <span class="subtitle">SETTINGS</span>
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
            <span class="user-role-badge" :class="role">{{ role === 'admin' ? t('common.admin') : t('common.user') }}</span>
          </div>
          <transition name="dropdown">
            <div v-if="showDropdown" class="dropdown-menu">
              <div class="dropdown-header">
                <div class="dropdown-avatar"><span>{{ username.charAt(0).toUpperCase() }}</span></div>
                <div class="dropdown-user-info">
                  <div class="dropdown-username">{{ username }}</div>
                  <div class="dropdown-role">{{ role === 'admin' ? t('common.admin') : t('common.user') }}</div>
                </div>
              </div>
              <div class="dropdown-divider"></div>
              <div class="dropdown-body">
                <div class="dropdown-item" @click="goToDashboard(); showDropdown = false">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                  <span>{{ t('nav.overview') }}</span>
                </div>
              </div>
              <div class="dropdown-divider"></div>
              <div class="dropdown-footer">
                <div class="dropdown-item logout-item" @click="logout">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                  <span>{{ t('common.logout') }}</span>
                </div>
              </div>
            </div>
          </transition>
          <button @click="logout" class="logout-btn" :title="t('common.logout')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      </div>
    </header>

    <div class="layout">
      <aside class="sidebar">
        <nav class="nav-menu">
          <a v-for="item in menuItems" :key="item.id" class="nav-item" :class="{ active: activeMenuValue === item.id }" @click="setActiveMenu(item.id)">
            <div class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" v-html="getNavIcon(item.icon)"/>
            </div>
            <div class="nav-text">
              <span class="nav-label">{{ t(item.i18nKey) }}</span>
              <span class="nav-desc">{{ item.desc }}</span>
            </div>
            <div class="nav-indicator" v-if="activeMenuValue === item.id"></div>
          </a>
        </nav>
        <div class="sidebar-footer">
          <button @click="goToDashboard" class="sidebar-back-btn">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
            <span>{{ t('nav.overview') }}</span>
          </button>
        </div>
      </aside>

      <main class="main-content">
        <transition name="fade" mode="out-in">
          <div :key="activeMenuValue" class="content-area">
            <div v-if="message.text" class="message-toast" :class="message.type">
              <svg v-if="message.type === 'success'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
              {{ message.text }}
            </div>

            <div v-if="activeMenuValue === 'profile'" class="settings-panel">
              <div class="panel-header"><h1>{{ t('settings.profile') }}</h1><p>{{ t('settings.profileDesc') }}</p></div>
              <div class="avatar-section">
                <div class="avatar-large"><span>{{ username.charAt(0).toUpperCase() }}</span></div>
                <div class="avatar-info"><div class="avatar-name">{{ username }}</div><div class="avatar-role">{{ role === 'admin' ? t('common.admin') : t('common.user') }}</div></div>
              </div>
              <div class="form-section">
                <div class="form-group"><label>{{ t('settings.username') }}</label><input type="text" :value="username" disabled class="input disabled" /><span class="form-hint">{{ t('settings.usernameHint') }}</span></div>
                <div class="form-group"><label>{{ t('settings.nickname') }}</label><input v-model="settingsForm.nickname" type="text" :placeholder="t('settings.nicknamePlaceholder')" class="input" /></div>
                <div class="form-group"><label>{{ t('settings.email') }}</label><input v-model="settingsForm.email" type="email" :placeholder="t('settings.emailPlaceholder')" class="input" /></div>
                <div class="form-group"><label>{{ t('settings.phone') }}</label><input v-model="settingsForm.phone" type="tel" :placeholder="t('settings.phonePlaceholder')" class="input" /></div>
              </div>
              <div class="form-actions"><button @click="handleSaveProfile" class="btn btn-primary">{{ t('settings.saveProfile') }}</button></div>
            </div>

            <div v-if="activeMenuValue === 'password'" class="settings-panel">
              <div class="panel-header"><h1>{{ t('settings.password') }}</h1><p>{{ t('settings.passwordDesc') }}</p></div>
              <div class="form-section">
                <div class="form-group"><label>{{ t('settings.currentPassword') }}</label><input v-model="settingsForm.currentPassword" type="password" :placeholder="t('settings.currentPasswordPlaceholder')" class="input" /></div>
                <div class="form-group">
                  <label>{{ t('settings.newPassword') }}</label>
                  <input v-model="settingsForm.newPassword" type="password" :placeholder="t('settings.newPasswordPlaceholder')" class="input" />
                  <div class="password-strength" v-if="settingsForm.newPassword">
                    <div class="strength-bar"><div class="strength-fill" :class="settingsForm.newPassword.length < 4 ? 'weak' : settingsForm.newPassword.length < 8 ? 'medium' : 'strong'" :style="{ width: Math.min(settingsForm.newPassword.length / 10 * 100, 100) + '%' }"></div></div>
                    <span class="strength-text" :class="settingsForm.newPassword.length < 4 ? 'weak' : settingsForm.newPassword.length < 8 ? 'medium' : 'strong'">{{ settingsForm.newPassword.length < 4 ? t('settings.weak') : settingsForm.newPassword.length < 8 ? t('settings.medium') : t('settings.strong') }}</span>
                  </div>
                </div>
                <div class="form-group"><label>{{ t('settings.confirmPassword') }}</label><input v-model="settingsForm.confirmPassword" type="password" :placeholder="t('settings.confirmPasswordPlaceholder')" class="input" /></div>
              </div>
              <div class="form-actions"><button @click="handleChangePassword" class="btn btn-warning">{{ t('settings.changePassword') }}</button></div>
            </div>

            <div v-if="activeMenuValue === 'security'" class="settings-panel">
              <div class="panel-header"><h1>{{ t('settings.security') }}</h1><p>{{ t('settings.securityDesc') }}</p></div>
              <div class="security-cards">
                <div class="security-card safe">
                  <div class="security-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
                  <div class="security-card-content"><h3>{{ t('settings.accountSecurityStatus') }}</h3><p>{{ t('settings.accountSecuritySafe') }}</p></div>
                  <div class="security-badge safe">{{ t('settings.strong') }}</div>
                </div>
                <div class="security-card">
                  <div class="security-card-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg></div>
                  <div class="security-card-content"><h3>{{ t('settings.passwordStrengthTip') }}</h3></div>
                </div>
              </div>
              <div class="danger-zone">
                <h2 class="section-title danger"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>{{ t('settings.dangerZone') }}</h2>
                <p class="danger-text">{{ t('settings.dangerZoneDesc') }}</p>
                <button class="btn btn-danger" disabled>{{ t('settings.deleteAccountDisabled') }}</button>
              </div>
            </div>

            <div v-if="activeMenuValue === 'appearance'" class="settings-panel">
              <div class="panel-header"><h1>{{ t('settings.appearance') }}</h1><p>{{ t('settings.appearanceDesc') }}</p></div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.theme') }}</h3>
                <div class="option-cards">
                  <div class="option-card" :class="{ active: appearanceSettings.theme === 'light' }" @click="appearanceSettings.theme = 'light'; saveAppearanceSettings()">
                    <div class="option-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg></div>
                    <span>{{ t('settings.themeLight') }}</span>
                    <svg v-if="appearanceSettings.theme === 'light'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" class="check-mark"><path d="M20 6L9 17l-5-5"/></svg>
                  </div>
                  <div class="option-card" :class="{ active: appearanceSettings.theme === 'dark' }" @click="appearanceSettings.theme = 'dark'; saveAppearanceSettings()">
                    <div class="option-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></div>
                    <span>{{ t('settings.themeDark') }}</span>
                    <svg v-if="appearanceSettings.theme === 'dark'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" class="check-mark"><path d="M20 6L9 17l-5-5"/></svg>
                  </div>
                  <div class="option-card" :class="{ active: appearanceSettings.theme === 'auto' }" @click="appearanceSettings.theme = 'auto'; saveAppearanceSettings()">
                    <div class="option-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg></div>
                    <span>{{ t('settings.themeAuto') }}</span>
                    <svg v-if="appearanceSettings.theme === 'auto'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" class="check-mark"><path d="M20 6L9 17l-5-5"/></svg>
                  </div>
                </div>
              </div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.accentColor') }}</h3>
                <div class="accent-color-list">
                  <div
                    v-for="color in accentColors"
                    :key="color.key"
                    class="accent-color-item"
                    :class="{ active: appearanceSettings.accentColor === color.key }"
                    @click="appearanceSettings.accentColor = color.key; saveAppearanceSettings()"
                  >
                    <div class="accent-color-dot" :style="{ background: color.value }"></div>
                    <span>{{ color.label }}</span>
                    <svg v-if="appearanceSettings.accentColor === color.key" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="14" height="14" class="accent-check"><polyline points="20 6 9 17 4 12"/></svg>
                  </div>
                </div>
              </div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.fontSize') }}</h3>
                <div class="option-cards compact">
                  <div class="option-card compact" :class="{ active: appearanceSettings.fontSize === 'small' }" @click="appearanceSettings.fontSize = 'small'; saveAppearanceSettings()"><span class="font-preview small">Aa</span><span>{{ t('settings.fontSizeSmall') }}</span></div>
                  <div class="option-card compact" :class="{ active: appearanceSettings.fontSize === 'medium' }" @click="appearanceSettings.fontSize = 'medium'; saveAppearanceSettings()"><span class="font-preview medium">Aa</span><span>{{ t('settings.fontSizeMedium') }}</span></div>
                  <div class="option-card compact" :class="{ active: appearanceSettings.fontSize === 'large' }" @click="appearanceSettings.fontSize = 'large'; saveAppearanceSettings()"><span class="font-preview large">Aa</span><span>{{ t('settings.fontSizeLarge') }}</span></div>
                </div>
              </div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.borderRadius') }}</h3>
                <div class="option-cards compact">
                  <div class="option-card compact" :class="{ active: appearanceSettings.borderRadius === 'small' }" @click="appearanceSettings.borderRadius = 'small'; saveAppearanceSettings()"><span class="radius-preview small-r"></span><span>{{ t('settings.borderRadiusSmall') }}</span></div>
                  <div class="option-card compact" :class="{ active: appearanceSettings.borderRadius === 'medium' }" @click="appearanceSettings.borderRadius = 'medium'; saveAppearanceSettings()"><span class="radius-preview medium-r"></span><span>{{ t('settings.borderRadiusMedium') }}</span></div>
                  <div class="option-card compact" :class="{ active: appearanceSettings.borderRadius === 'large' }" @click="appearanceSettings.borderRadius = 'large'; saveAppearanceSettings()"><span class="radius-preview large-r"></span><span>{{ t('settings.borderRadiusLarge') }}</span></div>
                </div>
              </div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.sidebarStyle') }}</h3>
                <div class="option-cards compact">
                  <div class="option-card compact" :class="{ active: appearanceSettings.sidebarStyle === 'expanded' }" @click="appearanceSettings.sidebarStyle = 'expanded'; saveAppearanceSettings()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
                    <span>{{ t('settings.sidebarExpanded') }}</span>
                  </div>
                  <div class="option-card compact" :class="{ active: appearanceSettings.sidebarStyle === 'collapsed' }" @click="appearanceSettings.sidebarStyle = 'collapsed'; saveAppearanceSettings()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="3" width="4" height="18" rx="1"/><rect x="9" y="3" width="12" height="18" rx="2"/></svg>
                    <span>{{ t('settings.sidebarCollapsed') }}</span>
                  </div>
                </div>
              </div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.backgroundPattern') }}</h3>
                <div class="option-cards compact">
                  <div class="option-card compact" :class="{ active: appearanceSettings.backgroundPattern === 'none' }" @click="appearanceSettings.backgroundPattern = 'none'; saveAppearanceSettings()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="3" x2="21" y2="21"/></svg>
                    <span>{{ t('settings.patternNone') }}</span>
                  </div>
                  <div class="option-card compact" :class="{ active: appearanceSettings.backgroundPattern === 'dots' }" @click="appearanceSettings.backgroundPattern = 'dots'; saveAppearanceSettings()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="7" cy="7" r="1.5"/><circle cx="17" cy="7" r="1.5"/><circle cx="7" cy="17" r="1.5"/><circle cx="17" cy="17" r="1.5"/><circle cx="12" cy="12" r="1.5"/></svg>
                    <span>{{ t('settings.patternDots') }}</span>
                  </div>
                  <div class="option-card compact" :class="{ active: appearanceSettings.backgroundPattern === 'grid' }" @click="appearanceSettings.backgroundPattern = 'grid'; saveAppearanceSettings()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>
                    <span>{{ t('settings.patternGrid') }}</span>
                  </div>
                  <div class="option-card compact" :class="{ active: appearanceSettings.backgroundPattern === 'stripes' }" @click="appearanceSettings.backgroundPattern = 'stripes'; saveAppearanceSettings()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><line x1="0" y1="6" x2="24" y2="6"/><line x1="0" y1="12" x2="24" y2="12"/><line x1="0" y1="18" x2="24" y2="18"/></svg>
                    <span>{{ t('settings.patternStripes') }}</span>
                  </div>
                </div>
              </div>
              <div class="settings-group">
                <div class="toggle-row">
                  <div class="toggle-info"><h3>{{ t('settings.animation') }}</h3><p>{{ appearanceSettings.animations ? t('settings.animationEnabled') : t('settings.animationDisabled') }}</p></div>
                  <label class="toggle-switch"><input type="checkbox" v-model="appearanceSettings.animations" @change="saveAppearanceSettings" /><span class="toggle-slider"></span></label>
                </div>
                <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.compactMode') }}</h3><p>{{ t('settings.compactModeDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="appearanceSettings.compactMode" @change="saveAppearanceSettings" /><span class="toggle-slider"></span></label></div>
              </div>
            </div>

            <div v-if="activeMenuValue === 'language'" class="settings-panel">
              <div class="panel-header"><h1>{{ t('settings.language') }}</h1><p>{{ t('settings.languageDesc') }}</p></div>
              <div class="settings-group">
                <div class="lang-current-banner">
                  <div class="lang-current-left">
                    <span class="lang-current-flag">{{ currentLocale.flag }}</span>
                    <div class="lang-current-info">
                      <span class="lang-current-name">{{ currentLocale.name }}</span>
                      <span class="lang-current-native">{{ currentLocale.nativeName }}</span>
                    </div>
                  </div>
                  <div class="lang-current-badge">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="20 6 9 17 4 12"/></svg>
                    {{ t('settings.currentLanguage') }}
                  </div>
                </div>
              </div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.selectLanguage') }}</h3>
                <div class="lang-list">
                  <div
                    v-for="lang in SUPPORTED_LOCALES"
                    :key="lang.code"
                    class="lang-item"
                    :class="{ active: locale === lang.code }"
                    @click="handleSelectLocale(lang.code)"
                  >
                    <span class="lang-item-flag">{{ lang.flag }}</span>
                    <div class="lang-item-info">
                      <span class="lang-item-name">{{ lang.name }}</span>
                      <span class="lang-item-native">{{ lang.nativeName }}</span>
                    </div>
                    <div v-if="locale === lang.code" class="lang-item-check">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="18" height="18"><polyline points="20 6 9 17 4 12"/></svg>
                    </div>
                    <div v-else class="lang-item-radio"></div>
                  </div>
                </div>
                <transition name="lang-msg">
                  <div v-if="languageChangedMsg" class="lang-changed-msg">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="20 6 9 17 4 12"/></svg>
                    {{ t('settings.languageChanged') }}
                  </div>
                </transition>
              </div>
              <div class="settings-group">
                <div class="lang-tip">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                  <span>{{ t('settings.languageSwitchNote') }}</span>
                </div>
              </div>
            </div>

            <div v-if="activeMenuValue === 'notification'" class="settings-panel">
              <div class="panel-header"><h1>{{ t('settings.notification') }}</h1><p>{{ t('settings.notificationDesc') }}</p></div>
              <div class="settings-group">
                <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.emailNotification') }}</h3><p>{{ t('settings.emailNotificationDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.emailNotification" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
                <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.borrowReminder') }}</h3><p>{{ t('settings.borrowReminderDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.borrowReminder" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
                <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.systemAnnouncement') }}</h3><p>{{ t('settings.systemAnnouncementDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.systemAnnouncement" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
                <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.dataReport') }}</h3><p>{{ t('settings.dataReportDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.dataReport" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
                <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.notificationSound') }}</h3><p>{{ t('settings.notificationSoundDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="notificationSettings.notificationSound" @change="saveNotificationSettings" /><span class="toggle-slider"></span></label></div>
              </div>
            </div>

            <div v-if="activeMenuValue === 'privacy'" class="settings-panel">
              <div class="panel-header"><h1>{{ t('settings.privacy') }}</h1><p>{{ t('settings.privacyDesc') }}</p></div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.profileVisibility') }}</h3>
                <div class="option-cards compact">
                  <div class="option-card compact" :class="{ active: privacySettings.profileVisibility === 'public' }" @click="privacySettings.profileVisibility = 'public'; savePrivacySettings()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                    <span>{{ t('settings.profilePublic') }}</span><span class="option-desc">{{ t('settings.profilePublicDesc') }}</span>
                  </div>
                  <div class="option-card compact" :class="{ active: privacySettings.profileVisibility === 'private' }" @click="privacySettings.profileVisibility = 'private'; savePrivacySettings()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    <span>{{ t('settings.profilePrivate') }}</span><span class="option-desc">{{ t('settings.profilePrivateDesc') }}</span>
                  </div>
                </div>
              </div>
              <div class="settings-group">
                <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.borrowHistory') }}</h3><p>{{ privacySettings.borrowHistoryVisible ? t('settings.borrowHistoryVisible') : t('settings.borrowHistoryHidden') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="privacySettings.borrowHistoryVisible" @change="savePrivacySettings" /><span class="toggle-slider"></span></label></div>
                <div class="toggle-row"><div class="toggle-info"><h3>{{ t('settings.dataCollection') }}</h3><p>{{ t('settings.dataCollectionDesc') }}</p></div><label class="toggle-switch"><input type="checkbox" v-model="privacySettings.dataCollection" @change="savePrivacySettings" /><span class="toggle-slider"></span></label></div>
              </div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.clearCache') }}</h3>
                <p class="group-desc">{{ t('settings.clearCacheDesc') }}</p>
                <button class="btn btn-outline" @click="handleClearCache">{{ t('settings.clearCacheBtn') }}</button>
              </div>
              <div class="settings-group">
                <h3 class="group-title">{{ t('settings.exportData') }}</h3>
                <p class="group-desc">{{ t('settings.exportDataDesc') }}</p>
                <button class="btn btn-outline">{{ t('settings.exportDataBtn') }}</button>
              </div>
            </div>

            <div v-if="activeMenuValue === 'about'" class="settings-panel">
              <div class="panel-header"><h1>{{ t('settings.about') }}</h1><p>{{ t('settings.aboutDesc') }}</p></div>
              <div class="about-card">
                <div class="about-logo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="48" height="48"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg></div>
                <h2>{{ t('common.systemTitle') }}</h2>
                <div class="about-version">v1.0.0</div>
              </div>
              <div class="about-info-list">
                <div class="about-info-item"><span class="info-label">{{ t('settings.systemVersion') }}</span><span class="info-value">1.0.0</span></div>
                <div class="about-info-item"><span class="info-label">{{ t('settings.buildDate') }}</span><span class="info-value">2026-04-22</span></div>
                <div class="about-info-item"><span class="info-label">{{ t('settings.frontend') }}</span><span class="info-value">Vue 3 + Vite</span></div>
                <div class="about-info-item"><span class="info-label">{{ t('settings.backend') }}</span><span class="info-value">FastAPI + Python</span></div>
                <div class="about-info-item"><span class="info-label">{{ t('settings.database') }}</span><span class="info-value">PostgreSQL</span></div>
              </div>
              <div class="about-footer">
                <div class="about-links">
                  <a href="#" class="about-link">{{ t('settings.openSourceLicense') }}</a>
                  <a href="#" class="about-link">{{ t('settings.contactUs') }}</a>
                  <a href="#" class="about-link">{{ t('settings.feedback') }}</a>
                </div>
              </div>
            </div>
          </div>
        </transition>
      </main>
    </div>

    <transition name="modal">
      <div v-if="showConfirmModal" class="modal-overlay" @click.self="handleCancelConfirm">
        <div class="modal-card">
          <h3>{{ t('common.confirm') || '\u786e\u8ba4' }}</h3>
          <p>{{ confirmMessage }}</p>
          <div class="modal-actions">
            <button class="btn btn-outline" @click="handleCancelConfirm">{{ t('settings.cancel') }}</button>
            <button class="btn btn-primary" @click="handleConfirm">{{ t('settings.save') }}</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>
<style scoped>
.settings-embedded { max-width: 720px; animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.settings-page { min-height: 100vh; background: var(--gradient-surface); font-family: var(--font-sans); }
.header { background: var(--gradient-glass); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); padding: 0 var(--space-6); display: flex; justify-content: space-between; align-items: center; height: var(--header-height); border-bottom: 1px solid var(--color-neutral-200); position: fixed; top: 0; left: 0; right: 0; z-index: var(--z-fixed); }
.header-left { display: flex; align-items: center; gap: var(--space-3); }
.back-btn { width: 36px; height: 36px; background: var(--color-neutral-100); border: 1px solid var(--color-neutral-200); border-radius: var(--radius-md); color: var(--color-neutral-500); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all var(--transition-base); }
.back-btn:hover { background: var(--color-neutral-200); color: var(--color-neutral-900); }
.back-btn svg { width: 18px; height: 18px; }
.logo-wrapper { display: flex; align-items: center; gap: var(--space-3); }
.logo-icon { width: 38px; height: 38px; background: var(--gradient-primary); border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-primary); }
.logo-icon svg { width: 22px; height: 22px; color: white; }
.title-group { display: flex; flex-direction: column; gap: 1px; }
.title-group h1 { font-size: var(--text-base); font-weight: var(--font-semibold); color: var(--color-neutral-900); margin: 0; }
.subtitle { font-size: var(--text-xs); color: var(--color-neutral-400); font-weight: var(--font-medium); letter-spacing: var(--tracking-wide); }
.header-right { display: flex; align-items: center; gap: var(--space-5); }
.datetime { display: flex; flex-direction: column; align-items: flex-end; }
.date { font-size: var(--text-sm); font-weight: var(--font-medium); color: var(--color-neutral-500); }
.user-menu { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-2) var(--space-3) var(--space-2) var(--space-2); background: var(--color-neutral-50); border-radius: var(--radius-xl); border: 1px solid var(--color-neutral-200); position: relative; }
.avatar { width: 34px; height: 34px; background: var(--gradient-primary); border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center; cursor: pointer; transition: all var(--transition-base); }
.avatar:hover { transform: scale(1.05); }
.avatar-text { color: white; font-size: var(--text-sm); font-weight: var(--font-semibold); }
.user-details { display: flex; flex-direction: column; gap: 2px; cursor: pointer; }
.user-name { font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--color-neutral-800); }
.user-role-badge { font-size: var(--text-xs); font-weight: var(--font-semibold); padding: 1px 6px; border-radius: var(--radius-sm); letter-spacing: var(--tracking-wide); }
.user-role-badge.admin { color: var(--color-primary-500); background: var(--color-primary-50); }
.user-role-badge.user { color: var(--color-success-500); background: var(--color-success-50); }
.dropdown-menu { position: absolute; top: calc(100% + 8px); right: 0; width: 240px; background: var(--color-neutral-0); border-radius: var(--radius-lg); box-shadow: var(--shadow-xl); border: 1px solid var(--color-neutral-200); overflow: hidden; z-index: var(--z-dropdown); }
.dropdown-header { display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4); background: var(--gradient-surface); border-bottom: 1px solid var(--color-neutral-200); }
.dropdown-avatar { width: 38px; height: 38px; background: var(--gradient-primary); border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.dropdown-avatar span { color: white; font-size: var(--text-base); font-weight: var(--font-semibold); }
.dropdown-user-info { display: flex; flex-direction: column; gap: 2px; }
.dropdown-username { font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--color-neutral-800); }
.dropdown-role { font-size: var(--text-xs); color: var(--color-neutral-500); }
.dropdown-divider { height: 1px; background: var(--color-neutral-200); }
.dropdown-body { padding: var(--space-2) 0; }
.dropdown-item { display: flex; align-items: center; gap: var(--space-3); padding: 10px var(--space-4); cursor: pointer; transition: all var(--transition-fast); color: var(--color-neutral-600); font-size: var(--text-sm); }
.dropdown-item:hover { background: var(--color-neutral-50); color: var(--color-primary-500); }
.dropdown-icon { width: 18px; height: 18px; flex-shrink: 0; }
.dropdown-footer { padding: var(--space-2) 0; }
.logout-item { color: var(--color-danger-500); }
.logout-item:hover { background: var(--color-danger-50); color: var(--color-danger-600); }
.dropdown-enter-active, .dropdown-leave-active { transition: all var(--transition-base); }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-8px) scale(0.96); }
.logout-btn { width: 32px; height: 32px; background: transparent; color: var(--color-neutral-400); border: none; border-radius: var(--radius-md); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all var(--transition-base); }
.logout-btn svg { width: 18px; height: 18px; }
.logout-btn:hover { background: var(--color-danger-50); color: var(--color-danger-500); }
.layout { display: flex; margin-top: var(--header-height); min-height: calc(100vh - var(--header-height)); }
.sidebar { width: var(--sidebar-width); background: var(--gradient-glass); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border-right: 1px solid var(--color-neutral-200); padding: var(--space-4) 0; display: flex; flex-direction: column; position: fixed; top: var(--header-height); bottom: 0; left: 0; overflow-y: auto; }
.nav-menu { flex: 1; padding: 0 var(--space-3); }
.nav-item { display: flex; align-items: center; gap: var(--space-3); padding: 10px var(--space-3); margin-bottom: 2px; border-radius: var(--radius-lg); cursor: pointer; transition: all var(--transition-base); position: relative; color: var(--color-neutral-500); text-decoration: none; }
.nav-item:hover { background: var(--color-neutral-50); color: var(--color-neutral-700); }
.nav-item.active { background: var(--color-primary-50); color: var(--color-primary-600); }
.nav-icon { width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.nav-icon svg { width: 20px; height: 20px; }
.nav-text { display: flex; flex-direction: column; gap: 1px; min-width: 0; }
.nav-label { font-size: var(--text-sm); font-weight: var(--font-medium); }
.nav-desc { font-size: var(--text-xs); color: var(--color-neutral-400); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nav-item.active .nav-desc { color: var(--color-primary-400); }
.nav-indicator { position: absolute; left: 0; top: 50%; transform: translateY(-50%); width: 3px; height: 20px; background: var(--gradient-primary); border-radius: 0 2px 2px 0; }
.sidebar-footer { padding: var(--space-3) var(--space-3); border-top: 1px solid var(--color-neutral-200); }
.sidebar-back-btn { display: flex; align-items: center; gap: var(--space-2); padding: 10px var(--space-4); background: var(--color-neutral-100); color: var(--color-neutral-600); border: 1px solid var(--color-neutral-200); border-radius: var(--radius-lg); cursor: pointer; font-size: var(--text-sm); font-weight: var(--font-medium); width: 100%; transition: all var(--transition-base); }
.sidebar-back-btn:hover { background: var(--color-primary-50); color: var(--color-primary-500); border-color: var(--color-primary-200); }
.sidebar-back-btn svg { width: 16px; height: 16px; }
.main-content { flex: 1; margin-left: var(--sidebar-width); padding: var(--space-8); min-height: calc(100vh - var(--header-height)); overflow-y: auto; }
.content-area { max-width: 720px; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.fade-enter-from { opacity: 0; transform: translateY(8px); }
.fade-leave-to { opacity: 0; transform: translateY(-8px); }
.message-toast { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-3) var(--space-4); border-radius: var(--radius-lg); margin-bottom: var(--space-6); font-size: var(--text-sm); font-weight: var(--font-medium); animation: slideDown 0.3s ease; }
.message-toast.success { background: var(--color-success-50); color: var(--color-success-700); border: 1px solid var(--color-success-200); }
.message-toast.error { background: var(--color-danger-50); color: var(--color-danger-700); border: 1px solid var(--color-danger-200); }
@keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
.settings-panel { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.panel-header { margin-bottom: var(--space-8); }
.panel-header h1 { font-size: var(--text-2xl); font-weight: var(--font-bold); color: var(--color-neutral-900); margin: 0 0 var(--space-2) 0; }
.panel-header p { font-size: var(--text-sm); color: var(--color-neutral-500); margin: 0; }
.avatar-section { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-5); background: var(--color-neutral-0); border-radius: var(--radius-xl); border: 1px solid var(--color-neutral-200); margin-bottom: var(--space-6); }
.avatar-large { width: 56px; height: 56px; background: var(--gradient-primary); border-radius: var(--radius-xl); display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-primary); }
.avatar-large span { color: white; font-size: var(--text-xl); font-weight: var(--font-bold); }
.avatar-info { display: flex; flex-direction: column; gap: 2px; }
.avatar-name { font-size: var(--text-lg); font-weight: var(--font-semibold); color: var(--color-neutral-900); }
.avatar-role { font-size: var(--text-sm); color: var(--color-neutral-500); }
.form-section { display: flex; flex-direction: column; gap: var(--space-5); }
.form-group { display: flex; flex-direction: column; gap: var(--space-2); }
.form-group label { font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--color-neutral-700); }
.input { padding: 10px 14px; border: 1px solid var(--color-neutral-300); border-radius: var(--radius-lg); font-size: var(--text-sm); color: var(--color-neutral-900); background: var(--color-neutral-0); transition: all var(--transition-fast); outline: none; }
.input:focus { border-color: var(--color-primary-400); box-shadow: 0 0 0 3px var(--color-primary-100); }
.input.disabled { background: var(--color-neutral-50); color: var(--color-neutral-400); cursor: not-allowed; }
.form-hint { font-size: var(--text-xs); color: var(--color-neutral-400); }
.password-strength { display: flex; align-items: center; gap: var(--space-2); }
.strength-bar { flex: 1; height: 4px; background: var(--color-neutral-200); border-radius: 2px; overflow: hidden; }
.strength-fill { height: 100%; border-radius: 2px; transition: all var(--transition-base); }
.strength-fill.weak { background: var(--color-danger-400); }
.strength-fill.medium { background: var(--color-warning-400); }
.strength-fill.strong { background: var(--color-success-400); }
.strength-text { font-size: var(--text-xs); font-weight: var(--font-semibold); }
.strength-text.weak { color: var(--color-danger-500); }
.strength-text.medium { color: var(--color-warning-500); }
.strength-text.strong { color: var(--color-success-500); }
.form-actions { margin-top: var(--space-6); display: flex; gap: var(--space-3); }
.btn { padding: 10px 20px; border-radius: var(--radius-lg); font-size: var(--text-sm); font-weight: var(--font-semibold); cursor: pointer; transition: all var(--transition-base); border: none; display: inline-flex; align-items: center; gap: var(--space-2); }
.btn-primary { background: var(--gradient-primary); color: white; box-shadow: var(--shadow-primary); }
.btn-primary:hover { box-shadow: var(--shadow-primary-lg); transform: translateY(-1px); }
.btn-warning { background: var(--color-warning-500); color: white; }
.btn-warning:hover { background: var(--color-warning-600); transform: translateY(-1px); }
.btn-danger { background: var(--color-danger-50); color: var(--color-danger-500); border: 1px solid var(--color-danger-200); }
.btn-danger:hover:not(:disabled) { background: var(--color-danger-100); }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-outline { background: var(--color-neutral-0); color: var(--color-neutral-700); border: 1px solid var(--color-neutral-300); }
.btn-outline:hover { background: var(--color-neutral-50); border-color: var(--color-primary-300); color: var(--color-primary-500); }
.security-cards { display: flex; flex-direction: column; gap: var(--space-4); margin-bottom: var(--space-8); }
.security-card { display: flex; align-items: center; gap: var(--space-4); padding: var(--space-5); background: var(--color-neutral-0); border-radius: var(--radius-xl); border: 1px solid var(--color-neutral-200); }
.security-card.safe { border-color: var(--color-success-200); background: var(--color-success-50); }
.security-card-icon { width: 44px; height: 44px; border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center; background: var(--color-neutral-100); flex-shrink: 0; }
.security-card.safe .security-card-icon { background: var(--color-success-100); color: var(--color-success-500); }
.security-card-icon svg { width: 22px; height: 22px; }
.security-card-content { flex: 1; }
.security-card-content h3 { font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--color-neutral-900); margin: 0 0 2px 0; }
.security-card-content p { font-size: var(--text-xs); color: var(--color-neutral-500); margin: 0; }
.security-badge { font-size: var(--text-xs); font-weight: var(--font-bold); padding: 4px 10px; border-radius: var(--radius-full); }
.security-badge.safe { background: var(--color-success-100); color: var(--color-success-600); }
.danger-zone { padding: var(--space-6); border: 1px solid var(--color-danger-200); border-radius: var(--radius-xl); background: var(--color-danger-50); }
.section-title { font-size: var(--text-base); font-weight: var(--font-semibold); color: var(--color-neutral-900); margin: 0 0 var(--space-3) 0; display: flex; align-items: center; gap: var(--space-2); }
.section-title.danger { color: var(--color-danger-600); }
.danger-text { font-size: var(--text-sm); color: var(--color-neutral-500); margin: 0 0 var(--space-4) 0; }
.settings-group { margin-bottom: var(--space-8); }
.group-title { font-size: var(--text-base); font-weight: var(--font-semibold); color: var(--color-neutral-900); margin: 0 0 var(--space-3) 0; }
.group-desc { font-size: var(--text-sm); color: var(--color-neutral-500); margin: 0 0 var(--space-4) 0; }
.option-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: var(--space-3); }
.option-card { display: flex; flex-direction: column; align-items: center; gap: var(--space-2); padding: var(--space-5); background: var(--color-neutral-0); border: 2px solid var(--color-neutral-200); border-radius: var(--radius-xl); cursor: pointer; transition: all var(--transition-base); position: relative; }
.option-card:hover { border-color: var(--color-primary-300); background: var(--color-primary-50); }
.option-card.active { border-color: var(--color-primary-400); background: var(--color-primary-50); box-shadow: 0 0 0 3px var(--color-primary-100); }
.option-card.compact { flex-direction: row; padding: var(--space-3) var(--space-4); gap: var(--space-3); }
.option-icon { width: 40px; height: 40px; border-radius: var(--radius-lg); display: flex; align-items: center; justify-content: center; background: var(--color-neutral-100); }
.option-icon svg { width: 22px; height: 22px; color: var(--color-neutral-500); }
.option-card.active .option-icon { background: var(--color-primary-100); }
.option-card.active .option-icon svg { color: var(--color-primary-500); }
.option-card span { font-size: var(--text-sm); font-weight: var(--font-medium); color: var(--color-neutral-700); }
.option-card.active span { color: var(--color-primary-600); }
.option-desc { font-size: var(--text-xs) !important; color: var(--color-neutral-400) !important; font-weight: var(--font-normal) !important; }
.check-mark { position: absolute; top: 8px; right: 8px; color: var(--color-primary-500); }
.font-preview { font-weight: var(--font-bold); color: var(--color-neutral-500); }
.font-preview.small { font-size: 12px; }
.font-preview.medium { font-size: 16px; }
.font-preview.large { font-size: 20px; }
.radius-preview { width: 20px; height: 20px; background: var(--color-neutral-300); flex-shrink: 0; }
.radius-preview.small-r { border-radius: 2px; }
.radius-preview.medium-r { border-radius: 6px; }
.radius-preview.large-r { border-radius: 12px; }
.accent-color-list { display: flex; flex-wrap: wrap; gap: var(--space-3); }
.accent-color-item { display: flex; align-items: center; gap: var(--space-2); padding: var(--space-2) var(--space-3); border: 2px solid var(--color-neutral-200); border-radius: var(--radius-lg); cursor: pointer; transition: all 0.2s ease; font-size: var(--text-sm); color: var(--color-neutral-700); }
.accent-color-item:hover { border-color: var(--color-neutral-300); background: var(--color-neutral-50); }
.accent-color-item.active { border-color: var(--color-primary-500); background: var(--color-primary-50); color: var(--color-primary-700); }
.accent-color-dot { width: 18px; height: 18px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 1px 3px rgba(0,0,0,0.15); }
.accent-check { color: var(--color-primary-500); }
.toggle-row { display: flex; align-items: center; justify-content: space-between; padding: var(--space-4) 0; border-bottom: 1px solid var(--color-neutral-100); }
.toggle-row:last-child { border-bottom: none; }
.toggle-info { flex: 1; }
.toggle-info h3 { font-size: var(--text-sm); font-weight: var(--font-semibold); color: var(--color-neutral-900); margin: 0 0 2px 0; }
.toggle-info p { font-size: var(--text-xs); color: var(--color-neutral-500); margin: 0; }
.toggle-switch { position: relative; display: inline-block; width: 44px; height: 24px; flex-shrink: 0; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background: var(--color-neutral-300); border-radius: 12px; transition: all var(--transition-base); }
.toggle-slider::before { content: ''; position: absolute; height: 18px; width: 18px; left: 3px; bottom: 3px; background: white; border-radius: 50%; transition: all var(--transition-base); box-shadow: var(--shadow-sm); }
.toggle-switch input:checked + .toggle-slider { background: var(--color-primary-500); }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(20px); }
.lang-current-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  background: linear-gradient(135deg, var(--color-primary-50), var(--color-primary-100));
  border: 1px solid var(--color-primary-200);
  border-radius: var(--radius-xl);
  margin-bottom: var(--space-4);
}
.lang-current-left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}
.lang-current-flag {
  font-size: 36px;
  line-height: 1;
}
.lang-current-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.lang-current-name {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  color: var(--color-primary-700);
}
.lang-current-native {
  font-size: var(--text-xs);
  color: var(--color-primary-400);
  font-weight: var(--font-medium);
}
.lang-current-badge {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  color: var(--color-primary-500);
  padding: 4px 10px;
  background: var(--color-primary-100);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-primary-200);
}
.lang-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.lang-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-neutral-0);
  border: 2px solid var(--color-neutral-200);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all var(--transition-base);
  position: relative;
}
.lang-item:hover {
  border-color: var(--color-primary-300);
  background: var(--color-primary-50);
  transform: translateX(4px);
}
.lang-item.active {
  border-color: var(--color-primary-400);
  background: var(--color-primary-50);
  box-shadow: 0 0 0 3px var(--color-primary-100);
}
.lang-item-flag {
  font-size: 28px;
  line-height: 1;
  width: 36px;
  text-align: center;
}
.lang-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.lang-item-name {
  font-size: var(--text-sm);
  font-weight: var(--font-semibold);
  color: var(--color-neutral-800);
}
.lang-item.active .lang-item-name {
  color: var(--color-primary-600);
}
.lang-item-native {
  font-size: var(--text-xs);
  color: var(--color-neutral-400);
}
.lang-item-check {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-primary-500);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.lang-item-radio {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--color-neutral-300);
  flex-shrink: 0;
  transition: all var(--transition-base);
}
.lang-item:hover .lang-item-radio {
  border-color: var(--color-primary-300);
}
.lang-tip {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  background: var(--color-neutral-50);
  border: 1px solid var(--color-neutral-200);
  border-radius: var(--radius-lg);
  color: var(--color-neutral-500);
  font-size: var(--text-sm);
  line-height: 1.5;
}
.lang-tip svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--color-neutral-400);
}

.lang-changed-msg {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  margin-top: var(--space-2);
  background: var(--color-success-50);
  border: 1px solid var(--color-success-200);
  border-radius: var(--radius-md);
  color: var(--color-success-600);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
}

.lang-msg-enter-active, .lang-msg-leave-active {
  transition: all 0.3s ease;
}

.lang-msg-enter-from, .lang-msg-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
.about-card { display: flex; flex-direction: column; align-items: center; gap: var(--space-3); padding: var(--space-8); background: var(--color-neutral-0); border-radius: var(--radius-xl); border: 1px solid var(--color-neutral-200); margin-bottom: var(--space-6); }
.about-logo { width: 72px; height: 72px; background: var(--gradient-primary); border-radius: var(--radius-xl); display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-primary); }
.about-logo svg { color: white; }
.about-card h2 { font-size: var(--text-lg); font-weight: var(--font-bold); color: var(--color-neutral-900); margin: 0; }
.about-version { font-size: var(--text-sm); color: var(--color-neutral-400); padding: 2px 10px; background: var(--color-neutral-100); border-radius: var(--radius-full); }
.about-info-list { background: var(--color-neutral-0); border-radius: var(--radius-xl); border: 1px solid var(--color-neutral-200); overflow: hidden; margin-bottom: var(--space-6); }
.about-info-item { display: flex; justify-content: space-between; align-items: center; padding: var(--space-4) var(--space-5); border-bottom: 1px solid var(--color-neutral-100); }
.about-info-item:last-child { border-bottom: none; }
.info-label { font-size: var(--text-sm); color: var(--color-neutral-500); }
.info-value { font-size: var(--text-sm); font-weight: var(--font-medium); color: var(--color-neutral-800); }
.about-footer { display: flex; justify-content: center; }
.about-links { display: flex; gap: var(--space-6); }
.about-link { font-size: var(--text-sm); color: var(--color-primary-500); text-decoration: none; transition: color var(--transition-fast); }
.about-link:hover { color: var(--color-primary-600); text-decoration: underline; }
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(4px); }
.modal-card { background: var(--color-neutral-0); border-radius: var(--radius-xl); padding: var(--space-6); width: 400px; max-width: 90vw; box-shadow: var(--shadow-xl); }
.modal-card h3 { font-size: var(--text-lg); font-weight: var(--font-semibold); color: var(--color-neutral-900); margin: 0 0 var(--space-3) 0; }
.modal-card p { font-size: var(--text-sm); color: var(--color-neutral-500); margin: 0 0 var(--space-5) 0; line-height: 1.5; }
.modal-actions { display: flex; justify-content: flex-end; gap: var(--space-3); }
.modal-enter-active, .modal-leave-active { transition: all 0.3s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-card, .modal-leave-to .modal-card { transform: scale(0.9); }
@media (max-width: 768px) {
  .sidebar { width: var(--sidebar-collapsed-width); }
  .sidebar .nav-text, .sidebar .sidebar-back-btn span { display: none; }
  .main-content { margin-left: var(--sidebar-collapsed-width); padding: var(--space-4); }
  .header-right .datetime { display: none; }
  .option-cards { grid-template-columns: 1fr; }
  .lang-current-banner { flex-direction: column; gap: var(--space-3); align-items: flex-start; }
  .lang-current-badge { align-self: flex-start; }
  .lang-item { padding: var(--space-3) var(--space-4); }
}
</style>
