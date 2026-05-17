import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as authApi from '../api/auth'
import type { UserPublic } from '../types/user'

const STORAGE_KEY = 'access_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(typeof localStorage !== 'undefined' ? localStorage.getItem(STORAGE_KEY) ?? '' : '')
  const user = ref<UserPublic | null>(null)

  const isAuthenticated = computed(() => Boolean(token.value))

  function setToken(t: string) {
    token.value = t
    localStorage.setItem(STORAGE_KEY, t)
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  async function hydrate() {
    if (!token.value) return
    try {
      user.value = await authApi.fetchMe()
    } catch {
      logout()
    }
  }

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    setToken(res.access_token)
    user.value = res.user
  }

  async function register(username: string, password: string) {
    const res = await authApi.register(username, password)
    setToken(res.access_token)
    user.value = res.user
  }

  async function refreshProfile() {
    user.value = await authApi.fetchMe()
  }

  return {
    token,
    user,
    isAuthenticated,
    setToken,
    logout,
    hydrate,
    login,
    register,
    refreshProfile,
  }
})
