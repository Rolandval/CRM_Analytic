import { useQuery, useMutation } from '@tanstack/react-query'
import { Phone, PhoneIncoming, PhoneOutgoing, Clock, RefreshCw, Loader2 } from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'
import { callsApi } from '../api/calls'
import { StatCard } from '../components/ui/StatCard'
import { PageSpinner } from '../components/ui/Spinner'

const PIE_COLORS = ['#3b82f6', '#8b5cf6', '#ef4444', '#f59e0b']

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['call-stats'],
    queryFn: callsApi.getStats,
    refetchInterval: 60_000,
  })

  const syncMutation = useMutation({
    mutationFn: callsApi.syncToday,
  })

  if (isLoading) return <PageSpinner />

  const stateData = Object.entries(stats?.by_state ?? {}).map(([name, value]) => ({ name, value }))
  const typeData = Object.entries(stats?.by_type ?? {}).map(([name, value]) => ({ name, value }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-0.5">Call center analytics overview</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
        >
          {syncMutation.isPending
            ? <Loader2 size={16} className="animate-spin" />
            : <RefreshCw size={16} />
          }
          Sync today
        </button>
      </div>

      {syncMutation.isSuccess && (
        <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg px-4 py-2 text-sm text-green-700 dark:text-green-300">
          Synced {syncMutation.data.stats.total} calls — {syncMutation.data.stats.new} new, {syncMutation.data.stats.updated} updated
        </div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total calls"
          value={stats?.total.toLocaleString() ?? '—'}
          icon={<Phone size={20} />}
          color="bg-blue-50 dark:bg-blue-950 text-blue-600 dark:text-blue-400"
        />
        <StatCard
          label="Inbound"
          value={stats?.by_type?.['CallType.INB']?.toLocaleString() ?? stats?.by_type?.IN?.toLocaleString() ?? '—'}
          icon={<PhoneIncoming size={20} />}
          color="bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400"
        />
        <StatCard
          label="Outbound"
          value={stats?.by_type?.['CallType.OUT']?.toLocaleString() ?? stats?.by_type?.OUT?.toLocaleString() ?? '—'}
          icon={<PhoneOutgoing size={20} />}
          color="bg-purple-50 dark:bg-purple-950 text-purple-600 dark:text-purple-400"
        />
        <StatCard
          label="Avg talk time"
          value={`${Math.round(stats?.avg_talk_duration_seconds ?? 0)}s`}
          icon={<Clock size={20} />}
          color="bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h2 className="text-sm font-semibold mb-4">Calls by State</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={stateData} cx="50%" cy="50%" outerRadius={80} dataKey="value" label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}>
                {stateData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h2 className="text-sm font-semibold mb-4">Calls by Type</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={typeData} barSize={40}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
