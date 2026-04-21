import { get, postForm } from './index'

export const authApi = {
  getCaptcha: () => get('/api/captcha'),

  login: (username, password, captcha, captchaKey) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    formData.append('captcha', captcha)
    formData.append('captcha_key', captchaKey)
    return postForm('/api/login', formData)
  },

  register: (username, password) => {
    const formData = new FormData()
    formData.append('username', username.trim())
    formData.append('password', password)
    return postForm('/api/register', formData)
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
  }
}
