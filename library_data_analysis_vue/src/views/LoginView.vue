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
      error.value = ''
    } else {
      error.value = t('login.captchaUnavailable')
    }
  } catch (e) {
    console.error('[Login] Failed to load captcha:', e)
    error.value = t('login.captchaConnectFail')
  }
}

onMounted(() => {
  const savedUsername = localStorage.getItem('remember_username')
  if (savedUsername) {
    username.value = savedUsername
    rememberMe.value = true
  }
  fetchCaptcha()
})

const handleLogin = async () => {
  error.value = ''
  
  if (!username.value || !password.value) {
    error.value = t('login.fillRequired')
    return
  }
  
  if (!captcha.value) {
    error.value = t('login.captchaRequired')
    return
  }
  
  loading.value = true

  try {
    console.log('[Login] Attempting login for:', username.value)
    
    const response = await authApi.login(
      username.value,
      password.value,
      captcha.value,
      captchaKey.value
    )

    if (response.ok) {
      const data = await response.json()
      
      console.log('[Login] Login successful, role:', data.role, 'system:', data.system)
      
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('username', data.username)
      localStorage.setItem('role', data.role)
      
      if (rememberMe.value) {
        localStorage.setItem('remember_username', username.value)
      } else {
        localStorage.removeItem('remember_username')
      }
      
      if (data.system === 'library') {
        router.push('/library')
      } else {
        router.push('/dashboard')
      }
    } else {
      const errData = await response.json()
      error.value = errData.detail || t('login.loginFailed')
      console.warn('[Login] Login failed:', error.value)
      captcha.value = ''
      fetchCaptcha()
    }
  } catch (e) {
    console.error('[Login] Network error:', e)
    if (e.name === 'AbortError') {
      error.value = t('login.requestTimeout')
    } else if (e.message && e.message.includes('fetch')) {
      error.value = t('login.networkError')
    } else {
      error.value = t('login.networkError')
    }
    fetchCaptcha()
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
          <h1>{{ t('login.heroTitle') }} · <span class="highlight">{{ t('login.heroHighlight') }}</span></h1>
          <p class="hero-desc">{{ t('login.heroDescUser') }}<br>{{ t('login.heroDescAdmin') }}</p>
        </div>

        <div class="features">
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div class="feature-title">{{ t('login.featureUserService') }}</div>
            <div class="feature-desc">{{ t('login.featureUserServiceDesc') }}</div>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
            </div>
            <div class="feature-title">{{ t('login.featureBookResource') }}</div>
            <div class="feature-desc">{{ t('login.featureBookResourceDesc') }}</div>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
            </div>
            <div class="feature-title">{{ t('login.featureDataAnalysis') }}</div>
            <div class="feature-desc">{{ t('login.featureDataAnalysisDesc') }}</div>
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
            <button type="button" class="btn-icon btn-secondary refresh-captcha" @click="fetchCaptcha">
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

          <button type="submit" class="btn btn-primary btn-lg btn-block submit-btn" :disabled="loading">
            {{ loading ? t('login.loggingIn') : t('login.loginBtn') }}
          </button>

          <div class="form-footer">
            <span>{{ t('login.noAccount') }}</span>
            <router-link to="/register" class="btn-ghost link-btn">{{ t('login.registerNow') }}</router-link>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
