import { ref, watch } from 'vue'
import { bookApi } from '@/api/books'
import { debounce } from '@/utils/timer'

export const useSearch = (delay = 500) => {
  const searchKeyword = ref('')
  const searchCategory = ref('')
  const searchResults = ref([])
  const searchTotal = ref(0)
  const searchPage = ref(1)
  const searchPageSize = ref(20)
  const searchTotalPages = ref(0)
  const searchLoading = ref(false)
  const hasSearched = ref(false)

  const performSearch = async (page = 1) => {
    searchLoading.value = true
    hasSearched.value = true
    searchPage.value = page
    try {
      const res = await bookApi.search(
        searchKeyword.value,
        searchCategory.value,
        page,
        searchPageSize.value
      )
      if (res.ok) {
        const data = await res.json()
        searchResults.value = data.books
        searchTotal.value = data.total
        searchTotalPages.value = data.total_pages
      }
    } catch (e) {
      console.error('检索失败', e)
    } finally {
      searchLoading.value = false
    }
  }

  const performAutoSearch = async (page = 1) => {
    hasSearched.value = true
    searchPage.value = page
    try {
      const res = await bookApi.search(
        searchKeyword.value,
        searchCategory.value,
        page,
        searchPageSize.value
      )
      if (res.ok) {
        const data = await res.json()
        searchResults.value = data.books
        searchTotal.value = data.total
        searchTotalPages.value = data.total_pages
      }
    } catch (e) {
      console.error('检索失败', e)
    }
  }

  const resetSearch = () => {
    searchKeyword.value = ''
    searchCategory.value = ''
    searchResults.value = []
    searchTotal.value = 0
    searchPage.value = 1
    searchTotalPages.value = 0
    hasSearched.value = false
    searchLoading.value = false
  }

  const debouncedSearch = debounce(() => performAutoSearch(1), delay)

  watch(searchKeyword, () => {
    if (searchKeyword.value.trim()) {
      debouncedSearch()
    }
  })

  return {
    searchKeyword,
    searchCategory,
    searchResults,
    searchTotal,
    searchPage,
    searchPageSize,
    searchTotalPages,
    searchLoading,
    hasSearched,
    performSearch,
    resetSearch
  }
}
