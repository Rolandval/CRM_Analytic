import type { ReactNode } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface Props {
  label: string
  value: string | number
  icon: ReactNode
  trend?: { value: number; positive: boolean }
  gradient?: string
  sublabel?: string
}

export function StatCard({ label, value, icon, trend, gradient, sublabel }: Props) {
  const defaultGradient = 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)'

  return (
    <div className="card-interactive p-5 animate-fade-in">
      <div className="flex items-start justify-between mb-4">
        {/* Icon */}
        <div
          className="w-11 h-11 rounded-xl flex items-center justify-center text-white shadow-sm flex-shrink-0"
          style={{ background: gradient ?? defaultGradient }}
        >
          {icon}
        </div>

        {/* Trend badge */}
        {trend && (
          <div className={`flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-xl ${
            trend.positive
              ? 'bg-emerald-50 text-emerald-600'
              : 'bg-rose-50 text-rose-600'
          }`}>
            {trend.positive ? <TrendingUp size={11} /> : <TrendingDown size={11} />}
            {trend.positive ? '+' : ''}{trend.value}%
          </div>
        )}
      </div>

      {/* Values */}
      <div>
        <p className="text-2xl font-bold text-slate-900 tracking-tight leading-none">{value}</p>
        <p className="text-sm text-slate-500 mt-1.5 font-medium">{label}</p>
        {sublabel && <p className="text-xs text-slate-400 mt-0.5">{sublabel}</p>}
      </div>
    </div>
  )
}
