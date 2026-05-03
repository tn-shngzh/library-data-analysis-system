import router from '../router'

const BASE_URL = ''
const TIMEOUT = 15000
const MAX_RETRIES = 2

interface CacheEntry {
  data: any
  timestamp: number
  staleTime: number
  maxAge: number
}

const swrCache = new Map<string, CacheEntry>()

const DEFAULT_STALE_TIME = 30 * 1000
const DEFAULT_MAX_AGE = 5 * 60 * 1000

const PATH_TTL_CONFIG: Record<string, { staleTime: number; maxAge: number }> = {
  '/api/overview/stats': { staleTime: 60 * 1000, maxAge: 5 * 60 * 1000 },
  '/api/overview/historical-stats': { staleTime: 2 * 60 * 1000, maxAge: 5 * 60 * 1000 },
  '/api/overview/categories': { staleTime: 5 * 60 * 1000, maxAge: 10 * 60 * 1000 },
  '/api/overview/top-books': { staleTime: 5 * 60 * 1000, maxAge: 10 * 60 * 1000 },
  '/api/borrows/stats': { staleTime: 60 * 1000, maxAge: 5 * 60 * 1000 },
  '/api/borrows/daily-trend': { staleTime: 5 * 60 * 1000, maxAge: 10 * 60 * 1000 },
  '/api/readers/monthly-trend': { staleTime: 5 * 60 * 1000, maxAge: 10 * 60 * 1000 },
  '/api/readers/top': { staleTime: 5 * 60 * 1000, maxAge: 10 * 60 * 1000 },
}

function getTTLConfig(url: string) {
  for (const [path, config] of Object.entries(PATH_TTL_CONFIG)) {
    if (url.startsWith(path)) return config
  }
  return { staleTime: DEFAULT_STALE_TIME, maxAge: DEFAULT_MAX_AGE }
}

const pendingRequests = new Map<string, Promise<any>>()

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

const rawRequest = async (url: string, options: RequestInit = {}, retries = 0): Promise<Response> => {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json'
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT)

  try {
    const response = await fetch(`${BASE_URL}${url}`, {
      ...options,
      headers,
      signal: controller.signal
    })

    if (response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      router.push('/login')
      throw new Error('认证已过期，请重新登录')
    }

    if (response.status >= 500 && retries < MAX_RETRIES) {
      await delay(1000)
      return rawRequest(url, options, retries + 1)
    }

    return response
  } catch (error: any) {
    if (error.message === '认证已过期，请重新登录') throw error
    if (retries < MAX_RETRIES) {
      await delay(1000)
      return rawRequest(url, options, retries + 1)
    }
    console.error(`请求失败: ${url}`, error)
    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

export const get = async (url: string): Promise<any> => {
  const config = getTTLConfig(url)
  const cached = swrCache.get(url)
  const now = Date.now()

  if (cached) {
    const age = now - cached.timestamp
    if (age < config.staleTime) {
      return cached.data
    }
    if (age < config.maxAge) {
      if (!pendingRequests.has(url)) {
        const bgPromise = rawRequest(url).then(async (res) => {
          if (res.ok) {
            const data = await res.json()
            swrCache.set(url, { data, timestamp: Date.now(), staleTime: config.staleTime, maxAge: config.maxAge })
            return data
          }
          throw new Error(`HTTP ${res.status}`)
        }).catch((err) => {
          console.warn(`Background revalidate failed for ${url}:`, err)
          return cached.data
        }).finally(() => {
          pendingRequests.delete(url)
        })
        pendingRequests.set(url, bgPromise)
      }
      return cached.data
    }
  }

  if (pendingRequests.has(url)) {
    return pendingRequests.get(url)!
  }

  const promise = rawRequest(url).then(async (res) => {
    if (res.ok) {
      const data = await res.json()
      swrCache.set(url, { data, timestamp: Date.now(), staleTime: config.staleTime, maxAge: config.maxAge })
      return data
    }
    throw new Error(`HTTP ${res.status}`)
  }).finally(() => {
    pendingRequests.delete(url)
  })

  pendingRequests.set(url, promise)
  return promise
}

export const post = async (url: string, body: any) => {
  invalidateCachePrefix('/api/')
  const res = await rawRequest(url, { method: 'POST', body: JSON.stringify(body) })
  if (res.ok) {
    return res.json()
  }
  throw new Error(`HTTP ${res.status}`)
}

export const postForm = async (url: string, formData: FormData) => {
  invalidateCachePrefix('/api/')
  const res = await rawRequest(url, { method: 'POST', body: formData })
  if (res.ok) {
    return res.json()
  }
  throw new Error(`HTTP ${res.status}`)
}

export const invalidateCachePrefix = (prefix: string) => {
  for (const key of swrCache.keys()) {
    if (key.startsWith(prefix)) {
      swrCache.delete(key)
    }
  }
}

export const invalidateCache = (url: string) => {
  swrCache.delete(url)
}
