import { get } from './index'

export const bookApi = {
  getStats: () => get('/api/books/stats'),
  getCategories: () => get('/api/books/categories'),
  getCategoriesList: () => get('/api/books/categories-list'),
  getHot: () => get('/api/books/hot'),
  search: (keyword, category, page = 1, pageSize = 20) =>
    get(`/api/books/search?keyword=${encodeURIComponent(keyword)}&category=${encodeURIComponent(category)}&page=${page}&page_size=${pageSize}`),

  getAll: async () => {
    const [statsRes, catRes, hotRes] = await Promise.all([
      bookApi.getStats(),
      bookApi.getCategories(),
      bookApi.getHot()
    ])

    const result = {}
    if (statsRes.ok) result.stats = await statsRes.json()
    if (catRes.ok) result.categories = await catRes.json()
    if (hotRes.ok) result.hotBooks = await hotRes.json()
    return result
  }
}
