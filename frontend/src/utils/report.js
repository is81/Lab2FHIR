/** 共享的报告类型工具函数 */

// 类型 → Element Plus Tag 颜色
export function getReportTypeColor(type) {
  const map = {
    '细胞学（妇科）': 'success',
    'HPV检测': 'warning',
    '细胞学（非妇科）': '',
    '常规病理': 'info',
  }
  return map[type] || ''
}

// 类型 → 标签
export function getReportTypeLabel(type) {
  return type || ''
}

// 格式化文件大小
export function formatFileSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
