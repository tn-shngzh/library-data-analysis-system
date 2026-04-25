<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { authApi } from '@/api/auth'
import '@/styles/login.css'

const { t } = useI18n()
const router = useRouter()
const username = ref('')
const password = ref('')
const captcha = ref('')
const captchaKey = ref('')
const captchaUrl = ref('')
const error = ref('')
const loading = ref(false)
const rememberMe = ref(false)

const fetchCaptcha = async () => {
  try {
    const response = await authApi.getCaptcha()
    if (response.ok) {
      const data = await response.json()
      captchaKey.value = data.key
      captchaUrl.value = data.image
    } else {
      error.value = t('login.captchaUnavailable')
    }
  } catch (e) {
    error.value = t('login.captchaConnectFail')
  }
}

onMounted(() => {
  fetchCaptcha()
})

const handleLogin = async () => {
  error.value = ''
  
  if (!captcha.value) {
    error.value = t('login.captchaRequired')
    return
  }
  
  loading.value = true

  try {
    const response = await authApi.login(
      username.value,
      password.value,
      captcha.value,
      captchaKey.value
    )

    if (response.ok) {
      const data = await response.json()
      
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('username', data.username)
      localStorage.setItem('role', data.role)
      
      if (rememberMe.value) {
        localStorage.setItem('remember_username', username.value)
      }
      
      if (data.system === 'library') {
        router.push('/library')
      } else {
        router.push('/dashboard')
      }
    } else {
      const errData = await response.json()
      error.value = errData.detail || t('login.loginFailed')
      captcha.value = ''
      fetchCaptcha()
    }
  } catch (e) {
    error.value = t('login.networkError')
    fetchCaptcha()
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
            {{ t('login.heroTitle') }} · <span class="highlight">{{ t('login.heroHighlight') }}</span>
          </h1>
          <p class="hero-desc">
            {{ t('login.heroDescUser') }}<br>
            {{ t('login.heroDescAdmin') }}
          </p>
        </div>

        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
              </svg>
            </div>
            <div class="feature-info">
              <div class="feature-name">{{ t('login.featureUserService') }}</div>
              <div class="feature-desc">{{ t('login.featureUserServiceDesc') }}</div>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"/>
              </svg>
            </div>
            <div class="feature-info">
              <div class="feature-name">{{ t('login.featureBookResource') }}</div>
              <div class="feature-desc">{{ t('login.featureBookResourceDesc') }}</div>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
              </svg>
            </div>
            <div class="feature-info">
              <div class="feature-name">{{ t('login.featureDataAnalysis') }}</div>
              <div class="feature-desc">{{ t('login.featureDataAnalysisDesc') }}</div>
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
          <h2>{{ t('login.welcomeTitle') }}</h2>
          <p>{{ t('login.welcomeDesc') }}</p>
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-item">
            <div class="input-wrapper">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <input 
                v-model="username" 
                type="text" 
                :placeholder="t('login.usernamePlaceholder')"
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
                :placeholder="t('login.passwordPlaceholder')"
                required
              />
            </div>
          </div>

          <div class="form-item captcha-row">
            <div class="input-wrapper captcha-input">
              <svg class="input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
              <input 
                v-model="captcha" 
                type="text" 
                :placeholder="t('login.captchaPlaceholder')"
                maxlength="4"
                required
              />
            </div>
            <div class="captcha-box" @click="fetchCaptcha">
              <img v-if="captchaUrl" :src="captchaUrl" :alt="t('login.captchaAlt')" />
              <span v-else>{{ t('login.loading') }}</span>
            </div>
            <button type="button" class="refresh-captcha" @click="fetchCaptcha">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="23 4 23 10 17 10"/>
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
              </svg>
            </button>
          </div>

          <div class="form-options">
            <label class="remember-me">
              <input type="checkbox" v-model="rememberMe" />
              <span>{{ t('login.rememberMe') }}</span>
            </label>
            <a href="#" class="forgot-password">{{ t('login.forgotPassword') }}</a>
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? t('login.loggingIn') : t('login.loginBtn') }}
          </button>

          <div class="form-footer">
            <span>{{ t('login.noAccount') }}</span>
            <router-link to="/register" class="link-btn">{{ t('login.registerNow') }}</router-link>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
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