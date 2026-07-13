import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// ====== 真实 API 函数 ======

// 获取统计数据
export async function getStats() {
  try {
    const { data } = await api.get('/stats')
    return data
  } catch {
    return { total: 0, type_counts: {}, recent: [] }
  }
}

// 获取报告列表
export async function getReports(params = {}) {
  try {
    const { data } = await api.get('/reports', { params })
    return data
  } catch {
    return { items: [], total: 0, page: 1, page_size: 10 }
  }
}

// 获取单个报告详情
export async function getReport(id) {
  try {
    const { data } = await api.get(`/reports/${id}`)
    return data
  } catch {
    return null
  }
}

// 上传PDF（单个）
export async function uploadPdf(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  try {
    const { data } = await api.post('/convert', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress
    })
    return data
  } catch (e) {
    return { success: false, error: e.response?.data?.detail || e.message }
  }
}

// 批量上传PDF
export async function uploadPdfBatch(files, onProgress) {
  const results = []
  let completed = 0
  for (const file of files) {
    const result = await uploadPdf(file)
    results.push({ file: file.name, ...result })
    completed++
    if (onProgress) {
      onProgress({ completed, total: files.length, file: file.name, result })
    }
  }
  const success = results.filter(r => r.success).length
  return { total: files.length, success, fail: files.length - success, results }
}

// 获取患者所有报告
export async function getPatientReports(name) {
  try {
    const { data } = await api.get(`/patients/${encodeURIComponent(name)}/reports`)
    return data
  } catch {
    return []
  }
}

// 搜索报告（快捷方法）
export async function searchReports(keyword, options = {}) {
  return getReports({ ...options, search: keyword })
}

export default api
