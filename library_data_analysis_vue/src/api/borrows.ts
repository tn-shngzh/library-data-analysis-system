import { get } from './index'

export const borrowApi = {
  getStats: () => get('/api/borrows/stats'),
  getActionStats: (params = '') => get(`/api/borrows/action-stats${params}`),
  getDegreeStats: (params = '') => get(`/api/borrows/degree-stats${params}`),
  getTopBorrowers: (params = '') => get(`/api/borrows/top-borrowers${params}`),
  getTopBooks: (params = '') => get(`/api/borrows/top-books${params}`),
  getRecent: (params = '') => get(`/api/borrows/recent${params}`),
  getMy: () => get('/api/borrows/my'),
  getDailyTrend: (params = '') => get(`/api/borrows/daily-trend${params}`),
  getMonthlyTrend: () => get('/api/borrows/monthly-trend'),
  getMonthlyReturns: () => get('/api/borrows/monthly-returns'),

  getAll: async () => {
    const result = {}
    const calls = [
      ['stats', borrowApi.getStats],
      ['actionStats', () => borrowApi.getActionStats()],
      ['degreeStats', () => borrowApi.getDegreeStats()],
      ['topBorrowers', () => borrowApi.getTopBorrowers()],
      ['topBooks', () => borrowApi.getTopBooks()],
      ['recentBorrows', () => borrowApi.getRecent()],
      ['monthlyBorrows', () => borrowApi.getMonthlyTrend()],
      ['monthlyReturns', () => borrowApi.getMonthlyReturns()]
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
