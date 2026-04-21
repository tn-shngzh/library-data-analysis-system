const BASE_URL = ''

const request = async (url, options = {}) => {
  const token = localStorage.getItem('token')
  const headers = { ...options.headers }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json'
  }

  try {
    const response = await fetch(`${BASE_URL}${url}`, { ...options, headers })

    if (response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('role')
      window.location.href = '/login'
      throw new Error('认证已过期，请重新登录')
    }

    return response
  } catch (error) {
    if (error.message === '认证已过期，请重新登录') throw error
    console.error(`请求失败: ${url}`, error)
    throw error
  }
}

export const get = (url) => request(url)

export const post = (url, body) =>
  request(url, { method: 'POST', body })

export const postForm = (url, formData) =>
  request(url, { method: 'POST', body: formData })
