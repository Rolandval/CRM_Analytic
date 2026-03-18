import { NavLink } from 'react-router-dom'
import { BarChart3, Phone, Users, Sun, Moon } from 'lucide-react'
import { useThemeStore } from '../../store/themeStore'

const NAV = [
  { to: '/', icon: BarChart3, label: 'Dashboard' },
  { to: '/calls', icon: Phone, label: 'Calls' },
  { to: '/users', icon: Users, label: 'Users' },
]

export function Sidebar() {
  const { dark, toggle } = useThemeStore()

  return (
    <aside className="flex flex-col w-56 min-h-screen bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 px-3 py-4">
      {/* Logo */}
      <div className="flex items-center gap-2 px-2 mb-8">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <Phone size={16} className="text-white" />
        </div>
        <span className="font-semibold text-slate-900 dark:text-white">CRM</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-50 dark:bg-blue-950 text-blue-700 dark:text-blue-300'
                  : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Theme toggle */}
      <div className="border-t border-slate-200 dark:border-slate-700 pt-3 mt-3">
        <button onClick={toggle} className="btn-ghost w-full justify-start">
          {dark ? <Sun size={16} /> : <Moon size={16} />}
          {dark ? 'Light mode' : 'Dark mode'}
        </button>
      </div>
    </aside>
  )
}
