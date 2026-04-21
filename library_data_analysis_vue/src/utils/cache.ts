export const CACHE_PREFIX = 'library_'
export const DEFAULT_CACHE_TTL = 10 * 60 * 1000

export const getCache = (key, ttl = DEFAULT_CACHE_TTL) => {
  const cached = localStorage.getItem(CACHE_PREFIX + key)
  const cachedTime = localStorage.getItem(CACHE_PREFIX + key + '_time')
  if (!cached || !cachedTime) return null

  const now = Date.now()
  if (now - parseInt(cachedTime) > ttl) {
    localStorage.removeItem(CACHE_PREFIX + key)
    localStorage.removeItem(CACHE_PREFIX + key + '_time')
    return null
  }

  try {
    return JSON.parse(cached)
  } catch {
    return null
  }
}

export const setCache = (key, data) => {
  localStorage.setItem(CACHE_PREFIX + key, JSON.stringify(data))
  localStorage.setItem(CACHE_PREFIX + key + '_time', Date.now().toString())
}

export const clearCache = (key) => {
  if (key) {
    localStorage.removeItem(CACHE_PREFIX + key)
    localStorage.removeItem(CACHE_PREFIX + key + '_time')
  } else {
    const keys = Object.keys(localStorage).filter(k => k.startsWith(CACHE_PREFIX))
    keys.forEach(k => localStorage.removeItem(k))
  }
}
