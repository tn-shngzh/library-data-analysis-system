import { get, postForm } from './index'

export const importsApi = {
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return postForm('/api/imports/upload', formData)
  },
  getHistory: () => get('/api/imports/history'),
  validate: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return postForm('/api/imports/validate', formData)
  }
}
