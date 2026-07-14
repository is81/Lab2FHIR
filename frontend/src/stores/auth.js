/** 认证状态管理（JWT + localStorage 持久化） */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/index.js'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('lab2fhir_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('lab2fhir_user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)
  const isPathologyStaff = computed(() => user.value?.role === 'pathology_staff')
  const isDoctor = computed(() => user.value?.role === 'doctor')
  const displayName = computed(() => user.value?.display_name || '')

  async function login(username, password) {
    const { data } = await api.post('/auth/login', { username, password })
    token.value = data.access_token
    user.value = data.user
    localStorage.setItem('lab2fhir_token', data.access_token)
    localStorage.setItem('lab2fhir_user', JSON.stringify(data.user))
    return data
  }

  async function fetchMe() {
    try {
      const { data } = await api.get('/auth/me')
      user.value = data
      localStorage.setItem('lab2fhir_user', JSON.stringify(data))
      return data
    } catch {
      logout()
      return null
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('lab2fhir_token')
    localStorage.removeItem('lab2fhir_user')
  }

  return {
    token, user,
    isAuthenticated, isPathologyStaff, isDoctor, displayName,
    login, fetchMe, logout
  }
})
