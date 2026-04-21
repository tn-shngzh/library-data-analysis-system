import { get } from './index'

export const overviewApi = {
  getStats: () => get('/api/overview/stats'),
  getCategories: () => get('/api/overview/categories'),
  getRecentBooks: () => get('/api/overview/recent-books'),

  getAll: async () => {
    const [statsRes, catRes, recentRes] = await Promise.all([
      overviewApi.getStats(),
      overviewApi.getCategories(),
      overviewApi.getRecentBooks()
    ])

    const result = {}
    if (statsRes.ok) result.stats = await statsRes.json()
    if (catRes.ok) result.categories = await catRes.json()
    if (recentRes.ok) result.recentBooks = await recentRes.json()
    return result
  }
}
