import { get } from './index'

export const readerApi = {
  getStats: () => get('/api/readers/stats'),
  getTypes: () => get('/api/readers/types'),
  getMonthlyTrend: () => get('/api/readers/monthly-trend'),
  getTop: () => get('/api/readers/top'),

  getAll: async () => {
    const result = {}
    const calls = [
      ['stats', readerApi.getStats],
      ['readerTypes', readerApi.getTypes],
      ['monthlyTrend', readerApi.getMonthlyTrend],
      ['topReaders', readerApi.getTop]
    ]
    const responses = await Promise.allSettled(calls.map(([, fn]) => fn()))
    for (let i = 0; i < calls.length; i++) {
      const [key] = calls[i]
      const res = responses[i]
      if (res.status === 'fulfilled') {
        result[key] = res.value
      } else {
        console.error(`readerApi.getAll: ${key} 请求失败`, res.reason)
      }
    }
    return result
  }
}
