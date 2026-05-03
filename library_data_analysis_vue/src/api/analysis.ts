import { get } from './index'

export const analysisApi = {
  getCorrelation: (year?: number) => {
    const params = year ? `?year=${year}` : ''
    return get(`/api/analysis/correlation${params}`)
  },
  getPeriodComparison: (p1Start?: number, p1End?: number, p2Start?: number, p2End?: number) => {
    const params = new URLSearchParams()
    if (p1Start) params.append('period1_start', p1Start.toString())
    if (p1End) params.append('period1_end', p1End.toString())
    if (p2Start) params.append('period2_start', p2Start.toString())
    if (p2End) params.append('period2_end', p2End.toString())
    const qs = params.toString()
    return get(`/api/analysis/period-comparison${qs ? '?' + qs : ''}`)
  },
  getCategoryHeatmap: (year?: number, months?: number) => {
    const params = new URLSearchParams()
    if (year) params.append('year', year.toString())
    if (months) params.append('months', months.toString())
    const qs = params.toString()
    return get(`/api/analysis/category-heatmap${qs ? '?' + qs : ''}`)
  }
}
