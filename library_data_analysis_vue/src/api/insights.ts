import { get } from './index'

export const insightsApi = {
  auto: (limit = 5) => get(`/api/insights/auto?limit=${limit}`)
}
