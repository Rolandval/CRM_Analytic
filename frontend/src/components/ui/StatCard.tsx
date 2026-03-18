import type { ReactNode } from 'react'

interface Props {
  label: string
  value: string | number
  icon: ReactNode
  trend?: { value: number; positive: boolean }
  color?: string
}

export function StatCard({ label, value, icon, color = 'bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400' }: Props) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
        <p className="text-2xl font-semibold text-slate-900 dark:text-white">{value}</p>
      </div>
    </div>
  )
}
