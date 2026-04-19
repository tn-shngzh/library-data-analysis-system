<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const role = ref('')

onMounted(() => {
  // 检查登录状态
  const token = localStorage.getItem('token')
  if (!token) {
    router.push('/login')
    return
  }
  
  username.value = localStorage.getItem('username') || ''
  role.value = localStorage.getItem('role') || ''
})

const logout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  router.push('/login')
}
</script>

<template>
  <div class="dashboard">
    <header class="header">
      <h1>图书馆数据分析系统</h1>
      <div class="user-info">
        <span>{{ username }} ({{ role }})</span>
        <button @click="logout">退出</button>
      </div>
    </header>
    
    <main class="main">
      <div class="placeholder">
        <h2>欢迎使用系统</h2>
        <p>V3 版本 - 系统功能开发中...</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: #f5f5f5;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header h1 {
  font-size: 18px;
  margin: 0;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info button {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.user-info button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.main {
  padding: 40px;
}

.placeholder {
  background: white;
  border-radius: 8px;
  padding: 60px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.placeholder h2 {
  color: #333;
  margin-bottom: 16px;
}

.placeholder p {
  color: #999;
}
</style>
