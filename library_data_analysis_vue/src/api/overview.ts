import { get } from './index'

export const overviewApi = {
  getStats: () => get('/api/overview/stats'),
  getCategories: () => get('/api/overview/categories'),
  getRecentBooks: () => get('/api/overview/recent-books'),

  getAll: async () => {
    const result = {}
    const calls = [
      ['stats', overviewApi.getStats],
      ['categories', overviewApi.getCategories],
      ['recentBooks', overviewApi.getRecentBooks]
    ]
    const responses = await Promise.allSettled(calls.map(([, fn]) => fn()))
    for (let i = 0; i < calls.length; i++) {
      const [key] = calls[i]
      const res = responses[i]
      if (res.status === 'fulfilled' && res.value.ok) {
        result[key] = await res.value.json()
      }
    }
    return result
  }
}
