import { create } from 'zustand'
import { useToastStore } from './toastStore'

export const useAuthStore = create((set) => ({
  token: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),

  setTokens: (accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    set({ token: accessToken, refreshToken, isAuthenticated: true })
  },

  // Обновление access_token по refresh_token — без тоста, это фоновая операция.
  setAccessToken: (accessToken) => {
    localStorage.setItem('access_token', accessToken)
    set({ token: accessToken, isAuthenticated: true })
  },

  logout: (options = {}) => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ token: null, refreshToken: null, isAuthenticated: false })
    if (!options.silent) {
      useToastStore.getState().addToast('Вы вышли из аккаунта', 'info')
    }
  },
}))
