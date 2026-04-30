import router from '../router'

const BASE_URL = ''
const TIMEOUT = 15000
const MAX_RETRIES = 2

const request = async (url, options = {}, retries = 0) => {
  const token = localStorage.getItem('token')
  const headers = { ...options.headers }

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

    return response
  } catch (error) {
    if (error.message === '认证已过期，请重新登录') throw error
    if (error.name === 'AbortError' && retries < MAX_RETRIES) {
      return request(url, options, retries + 1)
    }
    console.error(`请求失败: ${url}`, error)
    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

export const get = (url) => request(url)

export const post = (url, body) =>
  request(url, { method: 'POST', body })

export const postForm = (url, formData) =>
  request(url, { method: 'POST', body: formData })
