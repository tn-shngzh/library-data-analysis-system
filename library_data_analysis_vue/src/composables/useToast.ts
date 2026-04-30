import { ref } from 'vue'

const toasts = ref<{ id: number; message: string; type: 'success' | 'error'; visible: boolean }[]>([])
let nextId = 0

export const useToast = () => {
  const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    const id = nextId++
    toasts.value.push({ id, message, type, visible: true })
    setTimeout(() => {
      const idx = toasts.value.findIndex(t => t.id === id)
      if (idx !== -1) toasts.value.splice(idx, 1)
    }, 3000)
  }

  return { toasts, showToast }
}
