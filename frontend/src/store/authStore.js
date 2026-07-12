import { create } from 'zustand'

export const useAuthStore = create((set) => ({
  token: localStorage.getItem('access_token'),
  isAuthenticated: !!localStorage.getItem('access_token'),

  setToken: (token) => {
    localStorage.setItem('access_token', token)
    set({ token, isAuthenticated: true })
  },

  logout: () => {
    localStorage.removeItem('access_token')
    set({ token: null, isAuthenticated: false })
  },
}))
