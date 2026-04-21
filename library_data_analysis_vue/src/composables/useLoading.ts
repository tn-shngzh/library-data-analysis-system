import { ref } from 'vue'

export const useLoading = (initialState = true) => {
  const loading = ref(initialState)

  const withLoading = async (fn) => {
    loading.value = true
    try {
      return await fn()
    } catch (e) {
      console.error('操作失败', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  return { loading, withLoading }
}
