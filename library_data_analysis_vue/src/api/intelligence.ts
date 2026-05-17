import { get } from './index'

export interface CorrelationNode {
  id: string
  name: string
  category: string
  readers: number
  color: string
}

export interface CorrelationLink {
  source: string
  target: string
  value: number
  confidence: number
}

export interface CorrelationData {
  nodes: CorrelationNode[]
  links: CorrelationLink[]
  total_pairs: number
}

export interface OptimizationItem {
  bib_id: string
  name: string
  category: string
  borrow_count: number
  last_borrow_date: string | null
  issue_type: string
  issue_type_name: string
}

export interface OptimizationResponse {
  total: number
  page: number
  page_size: number
  total_pages: number
  list: OptimizationItem[]
}

export const intelligenceApi = {
  getCorrelation: (yearRange: string = 'all', minSupport: number = 0.05, limit: number = 150) => {
    const params = new URLSearchParams()
    params.append('year_range', yearRange)
    params.append('min_support', minSupport.toString())
    params.append('limit', limit.toString())
    const qs = params.toString()
    return get<CorrelationData>(`/api/intelligence/correlation?${qs}`)
  },

  getCollectionOptimization: (params: {
    never_borrowed?: boolean
    low_freq_threshold?: number
    idle_months?: number
    category?: string
    page?: number
    page_size?: number
  } = {}) => {
    const searchParams = new URLSearchParams()
    if (params.never_borrowed !== undefined) searchParams.append('never_borrowed', String(params.never_borrowed))
    if (params.low_freq_threshold !== undefined) searchParams.append('low_freq_threshold', String(params.low_freq_threshold))
    if (params.idle_months !== undefined) searchParams.append('idle_months', String(params.idle_months))
    if (params.category) searchParams.append('category', params.category)
    if (params.page !== undefined) searchParams.append('page', String(params.page))
    if (params.page_size !== undefined) searchParams.append('page_size', String(params.page_size))
    const qs = searchParams.toString()
    return get<OptimizationResponse>(`/api/intelligence/collection-optimization?${qs}`)
  }
}
