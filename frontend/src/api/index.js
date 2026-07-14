import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// ====== Request interceptor: 自动附加 JWT token ======
api.interceptors.request.use(config => {
  const token = localStorage.getItem('lab2fhir_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ====== Response interceptor: 401 跳转登录 + 通用错误提示 ======
api.interceptors.response.use(
  response => response,
  error => {
    // 401 → 清除 token 并跳转登录
    if (error.response?.status === 401) {
      localStorage.removeItem('lab2fhir_token')
      localStorage.removeItem('lab2fhir_user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
    const msg = error.response?.data?.detail || error.message || '网络请求失败'
    // 只在非静默模式下提示（upload/convert 需自行处理错误）
    if (!error.config?._silent) {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

// ====== API 函数（返回增强结构：{ data, error }） ======

// 获取统计数据
export async function getStats() {
  try {
    const { data } = await api.get('/stats')
    return { data, error: null }
  } catch (e) {
    return { data: { total: 0, type_counts: {}, recent: [] }, error: e.message }
  }
}

// 获取报告列表
export async function getReports(params = {}) {
  try {
    const { data } = await api.get('/reports', { params })
    return { data, error: null }
  } catch (e) {
    return { data: { items: [], total: 0, page: 1, page_size: 10 }, error: e.message }
  }
}

// 获取单个报告详情
export async function getReport(id) {
  try {
    const { data } = await api.get(`/reports/${id}`)
    return { data, error: null }
  } catch (e) {
    return { data: null, error: e.response?.status === 404 ? '报告不存在' : e.message }
  }
}

// 上传PDF（单个）
export async function uploadPdf(file, onProgress) {
  const formData = new FormData()
  formData.append('file', file)
  try {
    const { data } = await api.post('/convert', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
      _silent: true  // upload 错误由调用者处理
    })
    return data
  } catch (e) {
    return { success: false, error: e.response?.data?.detail || e.message }
  }
}

// 批量上传PDF（3.11 修复：并发控制，最多 3 个并发）
export async function uploadPdfBatch(files, onProgress) {
  const results = []
  let completed = 0
  const CONCURRENCY = 3

  // 使用信号量控制并发
  const semaphore = new Array(CONCURRENCY).fill(null).map(() => Promise.resolve())

  for (let i = 0; i < files.length; i++) {
    const file = files[i]
    // 等待一个空闲槽位
    const slot = semaphore[i % CONCURRENCY]
    semaphore[i % CONCURRENCY] = slot.then(async () => {
      const result = await uploadPdf(file)
      results[i] = { file: file.name, ...result }
      completed++
      if (onProgress) {
        onProgress({ completed, total: files.length, file: file.name, result })
      }
    }).catch(() => {
      results[i] = { file: file.name, success: false, error: '网络错误' }
      completed++
      if (onProgress) {
        onProgress({ completed, total: files.length, file: file.name, result: results[i] })
      }
    })
  }

  await Promise.all(semaphore)
  const success = results.filter(r => r.success).length
  return { total: files.length, success, fail: files.length - success, results }
}

// 获取患者所有报告
export async function getPatientReports(name) {
  try {
    const { data } = await api.get(`/patients/${encodeURIComponent(name)}/reports`)
    return { data, error: null }
  } catch (e) {
    return { data: [], error: e.message }
  }
}

// 搜索报告（快捷方法）
export async function searchReports(keyword, options = {}) {
  return getReports({ ...options, search: keyword })
}

export default api
