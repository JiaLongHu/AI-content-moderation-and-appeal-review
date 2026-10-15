import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { login as loginRequest } from '../api/auth'
import type { CurrentUser, LoginPayload } from '../types/auth'

function loadStoredUser(): CurrentUser | null {
  const value = localStorage.getItem('current_user')
  if (!value) return null
  try {
    return JSON.parse(value) as CurrentUser
  } catch {
    localStorage.removeItem('current_user')
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const user = ref<CurrentUser | null>(loadStoredUser())
  const isAuthenticated = computed(() => Boolean(token.value && user.value))

  async function login(payload: LoginPayload): Promise<CurrentUser> {
    const result = await loginRequest(payload)
    token.value = result.access_token
    user.value = result.user
    localStorage.setItem('access_token', result.access_token)
    localStorage.setItem('current_user', JSON.stringify(result.user))
    return result.user
  }

  function logout(): void {
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('current_user')
  }

  return { token, user, isAuthenticated, login, logout }
})

