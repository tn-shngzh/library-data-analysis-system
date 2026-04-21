import { get } from './index'

export const readerApi = {
  getStats: () => get('/api/readers/stats'),
  getTypes: () => get('/api/readers/types'),
  getMonthlyTrend: () => get('/api/readers/monthly-trend'),
  getTop: () => get('/api/readers/top'),

  getAll: async () => {
    const [statsRes, typesRes, trendRes, topRes] = await Promise.all([
      readerApi.getStats(),
      readerApi.getTypes(),
      readerApi.getMonthlyTrend(),
      readerApi.getTop()
    ])

    const result = {}
    if (statsRes.ok) result.stats = await statsRes.json()
    if (typesRes.ok) result.readerTypes = await typesRes.json()
    if (trendRes.ok) result.monthlyTrend = await trendRes.json()
    if (topRes.ok) result.topReaders = await topRes.json()
    return result
  }
}
