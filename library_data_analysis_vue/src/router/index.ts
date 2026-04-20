import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import OverviewView from '../views/OverviewView.vue'
import ReaderView from '../views/ReaderView.vue'
import BookView from '../views/BookView.vue'
import LibraryView from '../views/LibraryView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
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
      path: '/library',
      name: 'library',
      component: LibraryView
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView
    },
    {
      path: '/',
      component: DashboardView,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: OverviewView
        },
        {
          path: 'readers',
          name: 'readers',
          component: ReaderView
        },
        {
          path: 'books',
          name: 'books',
          component: BookView
        }
      ]
    }
  ]
})

export default router
