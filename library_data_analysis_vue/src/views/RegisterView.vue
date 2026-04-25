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
      <div class="left-content">
        <div class="brand">
          <div class="logo-icon-wrapper">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="28" height="28">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
          </div>
          <div class="brand-text">
            <div class="brand-title">{{ t('login.brandTitle') }}</div>
            <div class="brand-subtitle">{{ t('login.brandSubtitle') }}</div>
          </div>
        </div>

        <div class="hero">
          <h1>
            {{ t('login.heroTitle') }} · <span class="highlight">{{ t('register.heroHighlight') }}</span>
          </h1>
          <p class="hero-desc">
            {{ t('register.heroDesc1') }}<br>
            {{ t('register.heroDesc2') }}
          </p>
        </div>

        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
              </svg>
            </div>
            <div class="feature-info">
              <div class="feature-name">{{ t('register.featureQuick') }}</div>
              <div class="feature-desc">{{ t('register.featureQuickDesc') }}</div>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/>
              </svg>
            </div>
            <div class="feature-info">
              <div class="feature-name">{{ t('register.featureSecurity') }}</div>
              <div class="feature-desc">{{ t('register.featureSecurityDesc') }}</div>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
              </svg>
            </div>
            <div class="feature-info">
              <div class="feature-name">{{ t('register.featureInstant') }}</div>
              <div class="feature-desc">{{ t('register.featureInstantDesc') }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="copyright">
        © 2024 {{ t('login.copyright') }}
      </div>
    </div>

    <div class="login-right">
      <div class="login-card">
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

          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? t('register.registering') : t('register.registerBtn') }}
          </button>

          <div class="form-footer">
            <span>{{ t('register.hasAccount') }}</span>
            <router-link to="/login" class="link-btn">{{ t('register.loginNow') }}</router-link>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.success-message {
  background: var(--color-success-50);
  border: 1px solid var(--color-success-100);
  color: var(--color-success-600);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-5);
  font-size: var(--text-sm);
  animation: fadeInUp 0.3s ease;
}

.form-footer {
  text-align: center;
  margin-top: var(--space-6);
  font-size: var(--text-sm);
  color: var(--color-neutral-500);
}

.link-btn {
  color: var(--color-primary-500);
  text-decoration: none;
  font-weight: var(--font-medium);
  margin-left: var(--space-1);
  transition: color var(--transition-fast);
}

.link-btn:hover {
  color: var(--color-primary-600);
  text-decoration: underline;
}
</style>
