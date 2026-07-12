import { create } from 'zustand'

let nextId = 0

export const useToastStore = create((set, get) => ({
  toasts: [],

  addToast: (message, type = 'info') => {
    const id = nextId++
    const timeoutId = setTimeout(() => get().removeToast(id), 4000)
    set((state) => ({ toasts: [...state.toasts, { id, message, type, timeoutId }] }))
  },

  removeToast: (id) =>
    set((state) => {
      const toast = state.toasts.find((t) => t.id === id)
      if (toast?.timeoutId) clearTimeout(toast.timeoutId)
      return { toasts: state.toasts.filter((t) => t.id !== id) }
    }),

  pauseToast: (id) =>
    set((state) => ({
      toasts: state.toasts.map((t) => {
        if (t.id !== id || !t.timeoutId) return t
        clearTimeout(t.timeoutId)
        return { ...t, timeoutId: null }
      }),
    })),

  resumeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.map((t) => {
        if (t.id !== id || t.timeoutId) return t
        return { ...t, timeoutId: setTimeout(() => get().removeToast(id), 4000) }
      }),
    })),
}))
