import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ThemeState {
  dark: boolean
  toggle: () => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      dark: window.matchMedia('(prefers-color-scheme: dark)').matches,
      toggle: () => {
        const next = !get().dark
        document.documentElement.classList.toggle('dark', next)
        set({ dark: next })
      },
    }),
    { name: 'crm-theme' },
  ),
)

// Apply on load
const applyTheme = () => {
  const saved = JSON.parse(localStorage.getItem('crm-theme') || '{}')
  document.documentElement.classList.toggle('dark', saved?.state?.dark ?? false)
}
applyTheme()
