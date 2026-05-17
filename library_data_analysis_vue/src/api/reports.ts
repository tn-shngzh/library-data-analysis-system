import { get } from './index'

const getToken = () => localStorage.getItem('token')

const downloadFile = async (url: string, filename: string) => {
  const token = getToken()
  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch(url, { headers })
  if (!response.ok) {
    throw new Error(`下载失败: HTTP ${response.status}`)
  }

  const blob = await response.blob()
  const downloadUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = downloadUrl
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(downloadUrl)
}

export const reportApi = {
  checkStatus: () => get('/api/reports/status'),

  generateOverview: () => get('/api/reports/overview'),
  generateReader: () => get('/api/reports/reader'),
  generateBook: () => get('/api/reports/book'),
  generateBorrow: () => get('/api/reports/borrow'),

  exportExcel: (reportType: string) => {
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    const filename = `${reportType}_${ts}.xlsx`
    return downloadFile(`/api/reports/export/excel/${reportType}`, filename)
  },

  exportWord: (reportType: string, content: string) => {
    const params = new URLSearchParams({ report_type: reportType, content })
    const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
    const filename = `${reportType}_${ts}.docx`
    return downloadFile(`/api/reports/export/word?${params}`, filename)
  }
}
