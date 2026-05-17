import { get } from './index'

export const overviewApi = {
  getStats: (year?: number) => {
    const params = year ? `?year=${year}` : ''
    return get(`/api/overview/stats${params}`)
  },
  getHistoricalStats: () => get('/api/overview/historical-stats'),
  getCategories: () => get('/api/overview/book-categories'),
  getRecentBooks: () => get('/api/overview/recent-books'),
  getWeeklyTrend: (weeks = 12) => get(`/api/overview/weekly-trend?weeks=${weeks}`),
  getTopBooks: (limit = 10) => get(`/api/overview/top-books?limit=${limit}`),
  getMonthlyBorrows: (year?: number) => {
    const params = year ? `?year=${year}` : ''
    return get(`/api/overview/monthly-borrows${params}`)
  },
  getTrend7d: () => get('/api/overview/trend-7d'),
  getCollectionHealth: () => get('/api/overview/collection-health'),
  getReaderActivityHeatmap: () => get('/api/overview/reader-activity-heatmap'),
  getHistoricalDetail: () => get('/api/overview/historical-detail'),

  getAll: async (year?: number) => {
    const result: Record<string, any> = {}
    const calls = [
      ['stats', () => overviewApi.getStats(year)],
      ['historicalStats', overviewApi.getHistoricalStats],
      ['categories', overviewApi.getCategories],
      ['recentBooks', overviewApi.getRecentBooks],
      ['monthlyBorrows', () => overviewApi.getMonthlyBorrows(year)],
      ['trend7d', overviewApi.getTrend7d],
      ['collectionHealth', overviewApi.getCollectionHealth],
      ['readerActivityHeatmap', overviewApi.getReaderActivityHeatmap],
      ['historicalDetail', overviewApi.getHistoricalDetail]
    ]
    const responses = await Promise.allSettled(calls.map(([, fn]) => fn()))
    for (let i = 0; i < calls.length; i++) {
      const [key] = calls[i]
      const res = responses[i]
      if (res.status === 'fulfilled') {
        result[key] = res.value
      } else {
        console.error(`overviewApi.getAll: ${key} 请求失败`, res.reason)
      }
    }
    return result
  }
}
