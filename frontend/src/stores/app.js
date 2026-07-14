/** 全局应用状态：错误、加载状态管理 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const globalError = ref(null)
  const globalLoading = ref(false)

  function setError(msg) {
    globalError.value = msg
    if (msg) {
      setTimeout(() => { globalError.value = null }, 8000) // 8 秒自动清除
    }
  }

  function clearError() {
    globalError.value = null
  }

  function setLoading(v) {
    globalLoading.value = v
  }

  return { globalError, globalLoading, setError, clearError, setLoading }
})
