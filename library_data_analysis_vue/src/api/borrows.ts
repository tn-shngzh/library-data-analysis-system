import { get } from './index'

export const borrowApi = {
  getStats: () => get('/api/borrows/stats'),
  getActionStats: () => get('/api/borrows/action-stats'),
  getDegreeStats: () => get('/api/borrows/degree-stats'),
  getTopBorrowers: () => get('/api/borrows/top-borrowers'),
  getTopBooks: () => get('/api/borrows/top-books'),
  getRecent: () => get('/api/borrows/recent'),
  getMy: () => get('/api/borrows/my'),
  getDailyTrend: () => get('/api/borrows/daily-trend'),

  getAll: async () => {
    const result = {}
    const calls = [
      ['stats', borrowApi.getStats],
      ['actionStats', borrowApi.getActionStats],
      ['degreeStats', borrowApi.getDegreeStats],
      ['topBorrowers', borrowApi.getTopBorrowers],
      ['topBooks', borrowApi.getTopBooks],
      ['recentBorrows', borrowApi.getRecent]
    ]
    const responses = await Promise.allSettled(calls.map(([, fn]) => fn()))
    for (let i = 0; i < calls.length; i++) {
      const [key] = calls[i]
      const res = responses[i]
      if (res.status === 'fulfilled') {
        result[key] = res.value
      } else {
        console.error(`borrowApi.getAll: ${key} 请求失败`, res.reason)
      }
    }
    return result
  }
}
