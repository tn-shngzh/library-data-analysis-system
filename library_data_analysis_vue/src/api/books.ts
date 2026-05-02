import { get } from './index'

export const bookApi = {
  getStats: () => get('/api/books/stats'),
  getCategories: () => get('/api/books/categories'),
  getCategoriesList: () => get('/api/books/categories-list'),
  getHot: () => get('/api/books/hot'),
  search: (keyword, category, page = 1, pageSize = 20) =>
    get(`/api/books/search?keyword=${encodeURIComponent(keyword)}&category=${encodeURIComponent(category)}&page=${page}&page_size=${pageSize}`),

  getAll: async () => {
    const result = {}
    const calls = [
      ['stats', bookApi.getStats],
      ['categories', bookApi.getCategories],
      ['hotBooks', bookApi.getHot]
    ]
    const responses = await Promise.allSettled(calls.map(([, fn]) => fn()))
    for (let i = 0; i < calls.length; i++) {
      const [key] = calls[i]
      const res = responses[i]
      if (res.status === 'fulfilled') {
        result[key] = res.value
      } else {
        console.error(`bookApi.getAll: ${key} 请求失败`, res.reason)
      }
    }
    return result
  }
}
