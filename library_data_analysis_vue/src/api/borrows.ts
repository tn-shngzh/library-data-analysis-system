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
    const [statsRes, actionRes, degreeRes, topBorrowersRes, topBooksRes, recentRes] = await Promise.all([
      borrowApi.getStats(),
      borrowApi.getActionStats(),
      borrowApi.getDegreeStats(),
      borrowApi.getTopBorrowers(),
      borrowApi.getTopBooks(),
      borrowApi.getRecent()
    ])

    const result = {}
    if (statsRes.ok) result.stats = await statsRes.json()
    if (actionRes.ok) result.actionStats = await actionRes.json()
    if (degreeRes.ok) result.degreeStats = await degreeRes.json()
    if (topBorrowersRes.ok) result.topBorrowers = await topBorrowersRes.json()
    if (topBooksRes.ok) result.topBooks = await topBooksRes.json()
    if (recentRes.ok) result.recentBorrows = await recentRes.json()
    return result
  }
}
