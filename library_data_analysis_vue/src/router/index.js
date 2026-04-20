import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import DashboardView from '../views/DashboardView.vue'
import LibraryView from '../views/LibraryView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/login'
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true, role: 'admin' }
    },
    {
      path: '/library',
      name: 'library',
      component: LibraryView,
      meta: { requiresAuth: true, role: 'user' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  
  // 管理员才能访问数据分析系统
  if (to.path === '/dashboard' && role !== 'admin') {
    next('/library')
    return
  }
  
  // 普通用户不能访问数据分析系统
  if (to.path === '/library' && role === 'admin') {
    next('/dashboard')
    return
  }
  
  next()
})

export default router
