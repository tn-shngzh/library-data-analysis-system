<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { authApi } from '@/api/auth'
import '@/styles/login.css'

const { t } = useI18n()
const router = useRouter()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

const validateForm = () => {
  error.value = ''
  
  if (!username.value || username.value.trim().length === 0) {
    error.value = t('register.usernameRequired')
    return false
  }
  if (username.value.length < 3) {
    error.value = t('register.usernameMinLength')
    return false
  }
  if (username.value.length > 20) {
    error.value = t('register.usernameMaxLength')
    return false
  }
  if (!/^[a-zA-Z0-9_]+$/.test(username.value)) {
    error.value = t('register.usernamePattern')
    return false
  }
  
  if (!password.value || password.value.trim().length === 0) {
    error.value = t('register.passwordRequired')
    return false
  }
  if (password.value.length < 6) {
    error.value = t('register.passwordMinLength')
    return false
  }
  if (password.value.length > 50) {
    error.value = t('register.passwordMaxLength')
    return false
  }
  
  if (password.value !== confirmPassword.value) {
    error.value = t('register.passwordMismatch')
    return false
  }
  
  return true
}

const handleRegister = async () => {
  if (!validateForm()) {
    return
  }
  
  error.value = ''
  success.value = ''
  loading.value = true

  try {
    const response = await authApi.register(username.value, password.value)

    if (response.ok) {
      const data = await response.json()
      success.value = t('register.successMsg', { username: data.username })
      
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    } else {
      const errData = await response.json()
      error.value = errData.detail || t('register.registerFailed')
    }
  } catch (e) {
    error.value = t('register.networkError')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-left">
      <div class="left-bg-bookshelf">
        <svg viewBox="0 0 1200 400" fill="none" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMax slice">
          <rect x="50" y="20" width="18" height="180" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="72" y="40" width="14" height="160" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="90" y="10" width="20" height="190" rx="2" fill="currentColor" opacity="0.8"/>
          <rect x="114" y="50" width="12" height="150" rx="2" fill="currentColor" opacity="0.4"/>
          <rect x="130" y="25" width="16" height="175" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="200" y="30" width="22" height="170" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="226" y="15" width="15" height="185" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="245" y="45" width="18" height="155" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="267" y="20" width="13" height="180" rx="2" fill="currentColor" opacity="0.8"/>
          <rect x="350" y="35" width="20" height="165" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="374" y="10" width="16" height="190" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="394" y="50" width="14" height="150" rx="2" fill="currentColor" opacity="0.4"/>
          <rect x="412" y="20" width="19" height="180" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="500" y="25" width="17" height="175" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="521" y="40" width="21" height="160" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="546" y="15" width="13" height="185" rx="2" fill="currentColor" opacity="0.8"/>
          <rect x="563" y="55" width="16" height="145" rx="2" fill="currentColor" opacity="0.4"/>
          <rect x="650" y="20" width="18" height="180" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="672" y="45" width="15" height="155" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="691" y="10" width="20" height="190" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="715" y="35" width="14" height="165" rx="2" fill="currentColor" opacity="0.8"/>
          <rect x="800" y="30" width="22" height="170" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="826" y="15" width="16" height="185" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="846" y="50" width="18" height="150" rx="2" fill="currentColor" opacity="0.4"/>
          <rect x="868" y="20" width="13" height="180" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="950" y="25" width="20" height="175" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="974" y="40" width="15" height="160" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="993" y="10" width="19" height="190" rx="2" fill="currentColor" opacity="0.8"/>
          <rect x="1016" y="45" width="14" height="155" rx="2" fill="currentColor" opacity="0.4"/>
          <rect x="1100" y="20" width="18" height="180" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="1122" y="35" width="16" height="165" rx="2" fill="currentColor" opacity="0.7"/>
          <line x1="30" y1="200" x2="1170" y2="200" stroke="currentColor" stroke-width="3" opacity="0.5"/>
          <rect x="80" y="210" width="20" height="160" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="104" y="230" width="16" height="140" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="124" y="215" width="22" height="155" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="150" y="240" width="14" height="130" rx="2" fill="currentColor" opacity="0.4"/>
          <rect x="250" y="220" width="18" height="150" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="272" y="235" width="15" height="135" rx="2" fill="currentColor" opacity="0.8"/>
          <rect x="291" y="210" width="20" height="160" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="400" y="225" width="17" height="145" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="421" y="240" width="21" height="130" rx="2" fill="currentColor" opacity="0.4"/>
          <rect x="446" y="215" width="13" height="155" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="550" y="220" width="19" height="150" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="573" y="235" width="16" height="135" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="700" y="215" width="18" height="155" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="722" y="230" width="15" height="140" rx="2" fill="currentColor" opacity="0.8"/>
          <rect x="741" y="210" width="20" height="160" rx="2" fill="currentColor" opacity="0.4"/>
          <rect x="850" y="225" width="22" height="145" rx="2" fill="currentColor" opacity="0.7"/>
          <rect x="876" y="215" width="14" height="155" rx="2" fill="currentColor" opacity="0.5"/>
          <rect x="1000" y="220" width="18" height="150" rx="2" fill="currentColor" opacity="0.6"/>
          <rect x="1022" y="235" width="16" height="135" rx="2" fill="currentColor" opacity="0.8"/>
          <rect x="1042" y="210" width="20" height="160" rx="2" fill="currentColor" opacity="0.5"/>
          <line x1="30" y1="370" x2="1170" y2="370" stroke="currentColor" stroke-width="3" opacity="0.5"/>
        </svg>
      </div>

      <div class="left-bg-orb orb-3"></div>

      <div class="left-bg-floating-page">
        <svg width="60" height="80" viewBox="0 0 60 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="60" height="80" rx="3" fill="currentColor" opacity="0.8"/>
          <line x1="12" y1="16" x2="48" y2="16" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <line x1="12" y1="26" x2="42" y2="26" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <line x1="12" y1="36" x2="46" y2="36" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <line x1="12" y1="46" x2="38" y2="46" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <line x1="12" y1="56" x2="44" y2="56" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
        </svg>
      </div>
      <div class="left-bg-floating-page">
        <svg width="50" height="70" viewBox="0 0 50 70" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="50" height="70" rx="3" fill="currentColor" opacity="0.8"/>
          <line x1="10" y1="14" x2="40" y2="14" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <line x1="10" y1="24" x2="36" y2="24" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <line x1="10" y1="34" x2="38" y2="34" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <line x1="10" y1="44" x2="32" y2="44" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
        </svg>
      </div>
      <div class="left-bg-floating-page">
        <svg width="45" height="65" viewBox="0 0 45 65" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="45" height="65" rx="3" fill="currentColor" opacity="0.8"/>
          <line x1="9" y1="12" x2="36" y2="12" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <line x1="9" y1="22" x2="32" y2="22" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
          <line x1="9" y1="32" x2="34" y2="32" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
        </svg>
      </div>

      <div class="left-bg-particles">
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
        <div class="left-bg-particle"></div>
      </div>

      <div class="left-content">
        <div class="brand">
          <div class="logo-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
          </div>
          <div class="brand-text">
            <div class="brand-title">{{ t('login.brandTitle') }}</div>
            <div class="brand-subtitle">{{ t('login.brandSubtitle') }}</div>
          </div>
        </div>

        <div class="hero">
          <h1>{{ t('login.heroTitle') }} · <span class="highlight">{{ t('register.heroHighlight') }}</span></h1>
          <p class="hero-desc">{{ t('register.heroDesc1') }}<br>{{ t('register.heroDesc2') }}</p>
        </div>

        <div class="features">
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
              </svg>
            </div>
            <div class="feature-title">{{ t('register.featureQuick') }}</div>
            <div class="feature-desc">{{ t('register.featureQuickDesc') }}</div>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            <div class="feature-title">{{ t('register.featureSecurity') }}</div>
            <div class="feature-desc">{{ t('register.featureSecurityDesc') }}</div>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <div class="feature-title">{{ t('register.featureInstant') }}</div>
            <div class="feature-desc">{{ t('register.featureInstantDesc') }}</div>
          </div>
        </div>
      </div>

      <div class="copyright">© 2024 {{ t('login.copyright') }}</div>
    </div>

    <div class="login-right">
      <div class="login-card">
        <div class="login-icon">
          <div class="login-icon-wrapper">
            <div class="login-icon-glow"></div>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
            </svg>
          </div>
        </div>

        <div class="login-header">
          <h2>{{ t('register.createAccount') }}</h2>
          <p>{{ t('register.createAccountDesc') }}</p>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-if="success" class="success-message">
          {{ success }}
        </div>

        <form @submit.prevent="handleRegister" class="login-form">
          <div class="form-item">
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <input 
                v-model="username" 
                type="text" 
                :placeholder="t('register.usernamePlaceholder')"
                required
              />
            </div>
          </div>

          <div class="form-item">
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input 
                v-model="password" 
                type="password" 
                :placeholder="t('register.passwordPlaceholder')"
                required
              />
            </div>
          </div>

          <div class="form-item">
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                <path d="M12 16v-4"/>
                <path d="M12 8h.01"/>
              </svg>
              <input 
                v-model="confirmPassword" 
                type="password" 
                :placeholder="t('register.confirmPasswordPlaceholder')"
                required
              />
            </div>
          </div>

          <button type="submit" class="btn btn-primary btn-lg btn-block submit-btn" :disabled="loading">
            {{ loading ? t('register.registering') : t('register.registerBtn') }}
          </button>

          <div class="form-footer">
            <span>{{ t('register.hasAccount') }}</span>
            <router-link to="/login" class="btn-ghost link-btn">{{ t('register.loginNow') }}</router-link>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
