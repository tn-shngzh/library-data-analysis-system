<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Chart from 'chart.js/auto'

const router = useRouter()
const username = ref('管理员')

// 统计数据
const stats = ref({
  totalCirculations: 0,
  totalBorrowers: 0,
  totalBooks: 0,
  todayCirculations: 0
})

// 退出登录
const logout = async () => {
  await fetch('/api/logout')
  router.push('/login')
}

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await fetch('/api/stats')
    if (response.ok) {
      stats.value = await response.json()
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 加载图表
const loadCharts = async () => {
  try {
    // 借阅趋势
    const trendResponse = await fetch('/api/trends')
    const trendData = await trendResponse.json()

    new Chart(document.getElementById('trendChart') as HTMLCanvasElement, {
      type: 'line',
      data: {
        labels: trendData.months,
        datasets: [{
          label: '借阅次数',
          data: trendData.counts,
          borderColor: 'rgb(99, 102, 241)',
          backgroundColor: 'rgba(99, 102, 241, 0.1)',
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    })

    // 性别分布
    const genderResponse = await fetch('/api/gender-distribution')
    const genderData = await genderResponse.json()

    new Chart(document.getElementById('genderChart') as HTMLCanvasElement, {
      type: 'doughnut',
      data: {
        labels: ['女性', '男性', '未知'],
        datasets: [{
          data: [genderData.F, genderData.M, genderData.unknown],
          backgroundColor: ['rgb(236, 72, 153)', 'rgb(59, 130, 246)', 'rgb(156, 163, 175)']
        }]
      },
      options: { responsive: true }
    })
  } catch (error) {
    console.error('加载图表失败:', error)
  }
}

onMounted(() => {
  loadStats()
  loadCharts()
})
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <!-- 导航栏 -->
    <nav class="gradient-bg text-white shadow-lg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <svg class="w-8 h-8 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
            </svg>
            <span class="font-bold text-xl">图书馆数据分析系统</span>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm">欢迎, {{ username }}</span>
            <button
              @click="logout"
              class="bg-white text-purple-600 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-100 transition"
            >
              退出登录
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容 -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- 统计卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">总借阅记录</p>
              <p class="text-3xl font-bold text-gray-800">{{ stats.totalCirculations.toLocaleString() }}</p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
              </svg>
            </div>
          </div>
        </div>

        <div class="card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">注册读者</p>
              <p class="text-3xl font-bold text-gray-800">{{ stats.totalBorrowers.toLocaleString() }}</p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path>
              </svg>
            </div>
          </div>
        </div>

        <div class="card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">图书总量</p>
              <p class="text-3xl font-bold text-gray-800">{{ stats.totalBooks.toLocaleString() }}</p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
              </svg>
            </div>
          </div>
        </div>

        <div class="card p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500">今日借阅</p>
              <p class="text-3xl font-bold text-gray-800">{{ stats.todayCirculations.toLocaleString() }}</p>
            </div>
            <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <svg class="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- 图表区域 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="card p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">借阅趋势（按月）</h3>
          <canvas id="trendChart"></canvas>
        </div>

        <div class="card p-6">
          <h3 class="text-lg font-semibold text-gray-800 mb-4">读者性别分布</h3>
          <canvas id="genderChart"></canvas>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.gradient-bg {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}
</style>
