import { ref, onMounted, onUnmounted } from 'vue'
import { formatDate, formatDateTime } from '@/utils/format'

export const useTime = (format = 'date') => {
  const currentTime = ref('')
  let timer = null

  const updateTime = () => {
    const now = new Date()
    currentTime.value = format === 'datetime' ? formatDateTime(now) : formatDate(now)
  }

  onMounted(() => {
    updateTime()
    timer = setInterval(updateTime, 60000)
  })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })

  return { currentTime, updateTime }
}
