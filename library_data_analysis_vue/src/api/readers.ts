import { get } from './index'

export const readerApi = {
  getStats: () => get('/api/readers/stats'),
  getTypes: (params = '') => get(`/api/readers/types${params}`),
  getMonthlyTrend: (params = '') => get(`/api/readers/monthly-trend${params}`),
  getTop: (params = '') => get(`/api/readers/top${params}`),
  getDegreeStats: () => get('/api/readers/degree-stats'),
  getDegreeHourHeatmap: () => get('/api/readers/degree-hour-heatmap'),
  getFrequencyDistribution: () => get('/api/readers/frequency-distribution'),

  getAll: async () => {
    const result = {}
    const calls = [
      ['stats', readerApi.getStats],
      ['readerTypes', () => readerApi.getTypes()],
      ['monthlyTrend', () => readerApi.getMonthlyTrend()],
      ['topReaders', () => readerApi.getTop()],
      ['degreeStats', () => readerApi.getDegreeStats()],
      ['degreeHourHeatmap', () => readerApi.getDegreeHourHeatmap()],
      ['frequencyDistribution', () => readerApi.getFrequencyDistribution()]
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
