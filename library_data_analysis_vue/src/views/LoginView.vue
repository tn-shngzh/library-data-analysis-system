<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import bookIcon from '@/components/icons/book.png'
import '@/styles/login.css'

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
    const response = await fetch('/api/captcha')
    if (response.ok) {
      const data = await response.json()
      captchaKey.value = data.key
      captchaUrl.value = data.image
    } else {
      error.value = '验证码服务不可用'
    }
  } catch (e) {
    error.value = '无法连接验证码服务'
    console.error('获取验证码失败', e)
  }
}

onMounted(() => {
  fetchCaptcha()
})

const handleLogin = async () => {
  error.value = ''
  
  if (!captcha.value) {
    error.value = '请输入验证码'
    return
  }
  
  loading.value = true

  try {
    const formData = new FormData()
    formData.append('username', username.value)
    formData.append('password', password.value)
    formData.append('captcha', captcha.value)
    formData.append('captcha_key', captchaKey.value)

    const response = await fetch('/api/login', {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      const data = await response.json()
      
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('username', data.username)
      localStorage.setItem('role', data.role)
      
      if (rememberMe.value) {
        localStorage.setItem('remember_username', username.value)
      }
      
      // 根据角色跳转到不同系统
      if (data.system === 'library') {
        router.push('/library')
      } else {
        router.push('/dashboard')
      }
    } else {
      const errData = await response.json()
      error.value = errData.detail || '登录失败'
      captcha.value = ''
      fetchCaptcha()
    }
  } catch (e) {
    error.value = '网络错误，请重试'
    fetchCaptcha()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- 左侧区域 -->
    <div class="login-left">
      <div class="left-content">
        <!-- Logo -->
        <div class="brand">
          <img class="logo-icon" :src="bookIcon" alt="logo" />
          <div class="brand-text">
          <div class="brand-title">图书馆管理系统</div>
          <div class="brand-subtitle">Library Management System</div>
        </div>
        </div>

        <!-- 主标题 -->
        <div class="hero">
          <h1>
            智慧图书馆 · <span class="highlight">一站式服务</span>
          </h1>
          <p class="hero-desc">
            普通用户：在线借阅、查询图书、管理个人账户<br>
            管理员：数据分析、运营管理、决策支持
          </p>
        </div>

        <!-- 功能列表 -->
        <div class="features">
          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
              </svg>
            </div>
            <div class="feature-info">
              <div class="feature-name">用户服务</div>
              <div class="feature-desc">在线借阅查询管理</div>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"/>
              </svg>
            </div>
            <div class="feature-info">
              <div class="feature-name">图书资源</div>
              <div class="feature-desc">海量图书在线借阅</div>
            </div>
          </div>

          <div class="feature-item">
            <div class="feature-icon">
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/>
              </svg>
            </div>
            <div class="feature-info">
              <div class="feature-name">数据分析</div>
              <div class="feature-desc">管理决策支持</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 版权信息 -->
      <div class="copyright">
          © 2024 图书馆管理系统·让服务更智慧
        </div>
    </div>

    <!-- 右侧登录区域 -->
    <div class="login-right">
      <div class="login-card">
        <div class="login-header">
          <h2>欢迎登录</h2>
          <p>图书馆管理系统 - 根据您的角色自动进入相应系统</p>
        </div>

        <!-- 错误提示 -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <!-- 登录表单 -->
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
                placeholder="请输入用户名"
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
                placeholder="请输入密码"
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
                placeholder="请输入验证码"
                maxlength="4"
                required
              />
            </div>
            <div class="captcha-box" @click="fetchCaptcha">
              <img v-if="captchaUrl" :src="captchaUrl" alt="验证码" />
              <span v-else>加载中...</span>
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
              <span>记住我</span>
            </label>
            <a href="#" class="forgot-password">忘记密码?</a>
          </div>

          <button type="submit" class="submit-btn" :disabled="loading">
            {{ loading ? '登录中...' : '登录' }}
          </button>

          <div class="form-footer">
            <span>还没有账户？</span>
            <router-link to="/register" class="link-btn">立即注册</router-link>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.form-footer {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.875rem;
  color: #64748b;
}

.link-btn {
  color: #6366f1;
  text-decoration: none;
  font-weight: 500;
  margin-left: 0.25rem;
}

.link-btn:hover {
  color: #4f46e5;
  text-decoration: underline;
}
</style>
