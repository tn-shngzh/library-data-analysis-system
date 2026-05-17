import { get, post } from './index'

export const statisticsApi = {
  getFrequency(type = 'book', year = undefined) {
    const params = new URLSearchParams({ type })
    if (year !== undefined) params.set('year', String(year))
    return get(`/api/stats/frequency?${params}`)
  },

  getDescriptive(type = 'borrows', period = 'monthly', year = undefined) {
    const params = new URLSearchParams({ type, period })
    if (year !== undefined) params.set('year', String(year))
    return get(`/api/stats/descriptive?${params}`)
  },

  getCrossTabulation(row = 'category', col = 'action') {
    return get(`/api/stats/crosstab?row=${row}&col=${col}`)
  },

  getCorrelationMatrix() {
    return get('/api/stats/correlation-matrix')
  },

  getReaderClustering(nClusters = 4, year = undefined) {
    const params = new URLSearchParams({ n_clusters: String(nClusters) })
    if (year !== undefined) params.set('year', String(year))
    return get(`/api/stats/clustering/reader?${params}`)
  },

  getForecast(forecastDays = 7) {
    return get(`/api/stats/regression/forecast?forecast_days=${forecastDays}`)
  },

  async saveSnapshot(data: Record<string, any>) {
    const id = `snapshot_${Date.now()}`
    return post('/api/stats/snapshot', { id, ...data })
  }
}
