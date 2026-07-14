/** 报告搜索/筛选状态缓存，避免列表↔详情往返时重复请求 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getStats } from '../api/index.js'

export const useReportsStore = defineStore('reports', () => {
  // ====== 搜索筛选缓存 ======
  const lastSearchQuery = ref('')
  const lastFilterType = ref('')
  const lastPage = ref(1)
  const lastPageSize = ref(10)

  // ====== Dashboard 统计缓存（5 分钟有效） ======
  const statsCache = ref(null)
  const statsTimestamp = ref(0)

  async function fetchStats(force = false) {
    const now = Date.now()
    if (!force && statsCache.value && (now - statsTimestamp.value) < 300000) {
      return statsCache.value
    }
    const data = await getStats()
    statsCache.value = data
    statsTimestamp.value = now
    return data
  }

  function cacheSearchState(search, type, page, pageSize) {
    lastSearchQuery.value = search || ''
    lastFilterType.value = type || ''
    lastPage.value = page || 1
    lastPageSize.value = pageSize || 10
  }

  function clearSearchCache() {
    lastSearchQuery.value = ''
    lastFilterType.value = ''
    lastPage.value = 1
    lastPageSize.value = 10
  }

  function clearStatsCache() {
    statsCache.value = null
    statsTimestamp.value = 0
  }

  return {
    lastSearchQuery, lastFilterType, lastPage, lastPageSize,
    statsCache, statsTimestamp,
    fetchStats, cacheSearchState, clearSearchCache, clearStatsCache
  }
})
