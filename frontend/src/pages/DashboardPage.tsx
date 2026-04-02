import { useQuery, useMutation } from '@tanstack/react-query'
import {
  Phone, PhoneIncoming, PhoneOutgoing, Clock,
  RefreshCw, Loader2, CheckCircle2, Sparkles,
} from 'lucide-react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { callsApi } from '../api/calls'
import { StatCard } from '../components/ui/StatCard'
import { PageSpinner } from '../components/ui/Spinner'

const STATE_CFG: Record<string, { color: string; label: string }> = {
  ANSWER:   { color: '#10b981', label: 'Answered'  },
  NOANSWER: { color: '#94a3b8', label: 'No Answer' },
  BUSY:     { color: '#f59e0b', label: 'Busy'      },
  FAILED:   { color: '#f43f5e', label: 'Failed'    },
}

function formatSeconds(s: number) {
  if (!s) return '0s'
  const m = Math.floor(s / 60)
  const sec = Math.round(s % 60)
  return m ? `${m}m ${sec}s` : `${sec}s`
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number; payload: { name: string } }> }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white rounded-xl px-3.5 py-2.5 shadow-popover border border-black/[0.06]">
      <p className="text-xs text-slate-500 mb-0.5">{payload[0].payload.name}</p>
      <p className="text-sm font-bold text-slate-900">{payload[0].value.toLocaleString()}</p>
    </div>
  )
}

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['call-stats'],
    queryFn: callsApi.getStats,
    refetchInterval: 60_000,
  })

  const syncMutation = useMutation({ mutationFn: callsApi.syncToday })

  if (isLoading) return <PageSpinner />

  const stateData = Object.entries(stats?.by_state ?? {}).map(([key, value]) => ({
    key,
    name: STATE_CFG[key]?.label ?? key,
    value,
    color: STATE_CFG[key]?.color ?? '#94a3b8',
  }))

  const typeData = [
    {
      name: 'Inbound',
      value: stats?.by_type?.IN ?? stats?.by_type?.['CallType.INB'] ?? 0,
    },
    {
      name: 'Outbound',
      value: stats?.by_type?.OUT ?? stats?.by_type?.['CallType.OUT'] ?? 0,
    },
  ]

  const total = stats?.total ?? 0
  const answered = stats?.by_state?.ANSWER ?? 0
  const answerRate = total > 0 ? Math.round((answered / total) * 100) : 0

  return (
    <div className="space-y-6 animate-slide-up">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <span className="text-gradient">Dashboard</span>
          </h1>
          <p className="text-slate-500 text-sm mt-1">Call center analytics overview</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending}
        >
          {syncMutation.isPending
            ? <Loader2 size={15} className="animate-spin" />
            : <RefreshCw size={15} />
          }
          Sync today
        </button>
      </div>

      {/* Sync success */}
      {syncMutation.isSuccess && (
        <div className="flex items-center gap-3 bg-emerald-50 border border-emerald-200/70 rounded-2xl px-5 py-3.5 text-sm text-emerald-700 animate-slide-up shadow-sm">
          <CheckCircle2 size={16} className="flex-shrink-0" />
          <span>
            Synced <strong>{syncMutation.data.stats.total}</strong> calls —{' '}
            <strong>{syncMutation.data.stats.new} new</strong>, {syncMutation.data.stats.updated} updated
          </span>
        </div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Calls"
          value={total.toLocaleString()}
          icon={<Phone size={18} strokeWidth={2.5} />}
          gradient="linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)"
        />
        <StatCard
          label="Inbound"
          value={(stats?.by_type?.IN ?? stats?.by_type?.['CallType.INB'] ?? 0).toLocaleString()}
          icon={<PhoneIncoming size={18} strokeWidth={2.5} />}
          gradient="linear-gradient(135deg, #10b981 0%, #059669 100%)"
        />
        <StatCard
          label="Outbound"
          value={(stats?.by_type?.OUT ?? stats?.by_type?.['CallType.OUT'] ?? 0).toLocaleString()}
          icon={<PhoneOutgoing size={18} strokeWidth={2.5} />}
          gradient="linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)"
        />
        <StatCard
          label="Avg Talk Time"
          value={formatSeconds(stats?.avg_talk_duration_seconds ?? 0)}
          icon={<Clock size={18} strokeWidth={2.5} />}
          gradient="linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">

        {/* Donut chart */}
        <div className="card p-6 lg:col-span-3">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className="font-bold text-slate-900 text-base">Calls by State</h2>
              <p className="text-xs text-slate-400 mt-0.5">Distribution of call outcomes</p>
            </div>
            <div
              className="flex items-center gap-1.5 text-sm font-bold px-3.5 py-2 rounded-xl"
              style={{
                background: 'linear-gradient(135deg, rgba(16,185,129,0.12), rgba(5,150,105,0.08))',
                color: '#065f46',
              }}
            >
              <Sparkles size={13} />
              {answerRate}% answered
            </div>
          </div>

          <div className="flex items-center gap-8">
            <ResponsiveContainer width={200} height={200}>
              <PieChart>
                <Pie
                  data={stateData}
                  cx="50%" cy="50%"
                  innerRadius={60} outerRadius={90}
                  paddingAngle={4}
                  dataKey="value"
                  stroke="none"
                >
                  {stateData.map(entry => (
                    <Cell key={entry.key} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>

            {/* Legend */}
            <div className="flex-1 space-y-3">
              {stateData.map(entry => (
                <div key={entry.key} className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                         style={{ background: entry.color }} />
                    <span className="text-sm text-slate-600 font-medium">{entry.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">{entry.value.toLocaleString()}</span>
                    {total > 0 && (
                      <span className="text-xs text-slate-400">
                        {Math.round((entry.value / total) * 100)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bar chart */}
        <div className="card p-6 lg:col-span-2">
          <div className="mb-6">
            <h2 className="font-bold text-slate-900 text-base">Calls by Type</h2>
            <p className="text-xs text-slate-400 mt-0.5">Inbound vs outbound volume</p>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={typeData} barSize={52} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gradIn" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
                <linearGradient id="gradOut" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#7c3aed" />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#94a3b8', fontWeight: 500 }}
                     axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,0.03)', radius: 8 }} />
              <Bar dataKey="value" radius={[10, 10, 4, 4]}>
                <Cell fill="url(#gradIn)" />
                <Cell fill="url(#gradOut)" />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  )
}
