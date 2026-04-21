import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api/auth'

export const useAuth = () => {
  const router = useRouter()
  const username = ref('')
  const role = ref('')

  const loadUserInfo = () => {
    username.value = localStorage.getItem('username') || ''
    role.value = localStorage.getItem('role') || ''
  }

  const checkAuth = () => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return false
    }
    loadUserInfo()
    return true
  }

  const logout = () => {
    authApi.logout()
    router.push('/login')
  }

  onMounted(() => {
    loadUserInfo()
  })

  return { username, role, loadUserInfo, checkAuth, logout }
}
