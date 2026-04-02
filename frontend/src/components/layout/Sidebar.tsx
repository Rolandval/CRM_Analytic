import { NavLink } from 'react-router-dom'
import { BarChart3, Phone, Users, Sun, Moon, Zap } from 'lucide-react'
import { useThemeStore } from '../../store/themeStore'

const NAV = [
  { to: '/',       icon: BarChart3, label: 'Dashboard' },
  { to: '/calls',  icon: Phone,     label: 'Calls' },
  { to: '/users',  icon: Users,     label: 'Clients' },
]

export function Sidebar() {
  const { dark, toggle } = useThemeStore()

  return (
    <aside
      className="flex flex-col w-[220px] min-h-screen flex-shrink-0 px-3 py-5"
      style={{ background: 'linear-gradient(180deg, #0D0F14 0%, #111520 100%)' }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-2 mb-8">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0"
          style={{ background: 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)' }}
        >
          <Zap size={16} className="text-white" strokeWidth={2.5} />
        </div>
        <div>
          <p className="font-bold text-white text-[15px] tracking-tight leading-none">CallCRM</p>
          <p className="text-[10px] mt-0.5" style={{ color: 'rgba(255,255,255,0.35)' }}>Analytics Platform</p>
        </div>
      </div>

      {/* Nav label */}
      <p className="text-[10px] font-semibold uppercase tracking-[0.1em] px-3 mb-2"
         style={{ color: 'rgba(255,255,255,0.25)' }}>
        Navigation
      </p>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `nav-item ${isActive
                ? 'text-white'
                : 'hover:text-white'
              }`
            }
            style={({ isActive }) => isActive
              ? { background: 'rgba(99,102,241,0.18)', color: 'white' }
              : { color: 'rgba(255,255,255,0.5)' }
            }
          >
            {({ isActive }) => (
              <>
                {isActive && (
                  <div
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full"
                    style={{ background: 'linear-gradient(180deg, #6366f1, #3b82f6)' }}
                  />
                )}
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-150 ${
                  isActive ? 'opacity-100' : 'opacity-60 group-hover:opacity-80'
                }`}
                style={isActive
                  ? { background: 'linear-gradient(135deg, rgba(99,102,241,0.3), rgba(59,130,246,0.3))' }
                  : {}
                }>
                  <Icon size={15} strokeWidth={isActive ? 2.5 : 2} />
                </div>
                <span className="text-sm">{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Divider */}
      <div className="h-px mx-2 mb-3" style={{ background: 'rgba(255,255,255,0.07)' }} />

      {/* Theme toggle */}
      <button
        onClick={toggle}
        className="nav-item w-full"
        style={{ color: 'rgba(255,255,255,0.4)' }}
        onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.8)' }}
        onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.4)' }}
      >
        <div className="w-8 h-8 rounded-lg flex items-center justify-center"
             style={{ background: 'rgba(255,255,255,0.06)' }}>
          {dark ? <Sun size={14} /> : <Moon size={14} />}
        </div>
        <span className="text-sm">{dark ? 'Light mode' : 'Dark mode'}</span>
      </button>
    </aside>
  )
}
