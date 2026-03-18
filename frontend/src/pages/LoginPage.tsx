import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Phone, Loader2 } from 'lucide-react'
import { authApi } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const [form, setForm] = useState({ username: '', password: '' })
  const navigate = useNavigate()
  const { setToken, setUser } = useAuthStore()

  const loginMutation = useMutation({
    mutationFn: () => authApi.login(form),
    onSuccess: async (data) => {
      setToken(data.access_token)
      const me = await authApi.me()
      setUser(me)
      navigate('/')
    },
  })

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
      <div className="card p-8 w-full max-w-sm">
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
            <Phone size={24} className="text-white" />
          </div>
        </div>
        <h1 className="text-xl font-semibold text-center mb-1">Welcome back</h1>
        <p className="text-sm text-slate-500 text-center mb-6">Sign in to CRM Dashboard</p>

        <form
          onSubmit={(e) => { e.preventDefault(); loginMutation.mutate() }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium mb-1">Username</label>
            <input
              className="input"
              value={form.username}
              onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
              autoFocus
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              className="input"
              value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
              required
            />
          </div>
          {loginMutation.isError && (
            <p className="text-sm text-red-600 dark:text-red-400">
              Invalid username or password
            </p>
          )}
          <button type="submit" className="btn-primary w-full justify-center" disabled={loginMutation.isPending}>
            {loginMutation.isPending ? <Loader2 size={16} className="animate-spin" /> : null}
            Sign in
          </button>
        </form>
      </div>
    </div>
  )
}
