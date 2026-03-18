import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { AdminUser } from '../api/types'

interface AuthState {
  token: string | null
  user: AdminUser | null
  setToken: (token: string) => void
  setUser: (user: AdminUser) => void
  logout: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      setToken: (token) => {
        localStorage.setItem('access_token', token)
        set({ token })
      },
      setUser: (user) => set({ user }),
      logout: () => {
        localStorage.removeItem('access_token')
        set({ token: null, user: null })
      },
      isAuthenticated: () => !!get().token,
    }),
    { name: 'crm-auth', partialize: (s) => ({ token: s.token, user: s.user }) },
  ),
)
