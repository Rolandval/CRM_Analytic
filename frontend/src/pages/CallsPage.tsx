import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Search, Filter, X } from 'lucide-react'
import { format } from 'date-fns'
import { callsApi } from '../api/calls'
import type { CallFilters, CallState, CallType } from '../api/types'
import { CallStateBadge } from '../components/calls/CallStateBadge'
import { CallTypeBadge } from '../components/calls/CallTypeBadge'
import { Pagination } from '../components/ui/Pagination'
import { PageSpinner } from '../components/ui/Spinner'

const STATES: CallState[] = ['ANSWER', 'NOANSWER', 'BUSY', 'FAILED']
const TYPES: { value: CallType; label: string }[] = [
  { value: 'IN', label: 'Inbound' },
  { value: 'OUT', label: 'Outbound' },
]

function formatDuration(s: number) {
  if (!s) return '—'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return m ? `${m}m ${sec}s` : `${sec}s`
}

export default function CallsPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<Omit<CallFilters, 'page' | 'page_size'>>({})
  const [search, setSearch] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  const { data, isLoading } = useQuery({
    queryKey: ['calls', page, filters, search],
    queryFn: () => callsApi.list({ ...filters, search: search || undefined, page, page_size: 25 }),
  })

  const setFilter = (k: keyof typeof filters, v: unknown) =>
    setFilters(f => ({ ...f, [k]: v || undefined }))

  const clearFilters = () => { setFilters({}); setSearch('') }
  const hasFilters = Object.keys(filters).length > 0 || search

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Calls</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {data?.total.toLocaleString() ?? '…'} calls total
          </p>
        </div>
      </div>

      {/* Search + filter bar */}
      <div className="card p-3 flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
          <input
            className="input pl-8"
            placeholder="Search by number…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <button className="btn-ghost" onClick={() => setShowFilters(!showFilters)}>
          <Filter size={14} /> Filters
          {hasFilters && <span className="w-2 h-2 bg-blue-600 rounded-full" />}
        </button>
        {hasFilters && (
          <button className="btn-ghost text-red-500" onClick={clearFilters}>
            <X size={14} /> Clear
          </button>
        )}
      </div>

      {/* Expanded filters */}
      {showFilters && (
        <div className="card p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">State</label>
            <select className="input" value={filters.call_state ?? ''} onChange={e => setFilter('call_state', e.target.value as CallState)}>
              <option value="">All</option>
              {STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Type</label>
            <select className="input" value={filters.call_type ?? ''} onChange={e => setFilter('call_type', e.target.value as CallType)}>
              <option value="">All</option>
              {TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Date from</label>
            <input type="datetime-local" className="input" value={filters.date_from ?? ''} onChange={e => setFilter('date_from', e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Date to</label>
            <input type="datetime-local" className="input" value={filters.date_to ?? ''} onChange={e => setFilter('date_to', e.target.value)} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Min duration (s)</label>
            <input type="number" min={0} className="input" value={filters.min_duration ?? ''} onChange={e => setFilter('min_duration', e.target.value ? Number(e.target.value) : undefined)} />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 mb-1 block">Max duration (s)</label>
            <input type="number" min={0} className="input" value={filters.max_duration ?? ''} onChange={e => setFilter('max_duration', e.target.value ? Number(e.target.value) : undefined)} />
          </div>
        </div>
      )}

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? <PageSpinner /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-700 text-xs text-slate-500 uppercase tracking-wider">
                  <th className="text-left px-4 py-3">ID</th>
                  <th className="text-left px-4 py-3">Type</th>
                  <th className="text-left px-4 py-3">State</th>
                  <th className="text-left px-4 py-3">From</th>
                  <th className="text-left px-4 py-3">To</th>
                  <th className="text-left px-4 py-3">Date</th>
                  <th className="text-left px-4 py-3">Duration</th>
                  <th className="text-left px-4 py-3">Recording</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {data?.items.map(call => (
                  <tr
                    key={call.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/calls/${call.id}`)}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">{call.id}</td>
                    <td className="px-4 py-3"><CallTypeBadge type={call.call_type} /></td>
                    <td className="px-4 py-3"><CallStateBadge state={call.call_state} /></td>
                    <td className="px-4 py-3 font-mono">{call.from_number ?? '—'}</td>
                    <td className="px-4 py-3 font-mono">{call.to_number ?? '—'}</td>
                    <td className="px-4 py-3 text-slate-500">
                      {call.date ? format(new Date(call.date), 'dd MMM yyyy HH:mm') : '—'}
                    </td>
                    <td className="px-4 py-3">{formatDuration(call.seconds_talktime)}</td>
                    <td className="px-4 py-3">
                      {call.mp3_link
                        ? <span className="badge bg-green-50 text-green-700 dark:bg-green-900 dark:text-green-300">MP3</span>
                        : <span className="text-slate-400">—</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data?.items.length === 0 && (
              <div className="text-center py-12 text-slate-400">No calls found</div>
            )}
          </div>
        )}
      </div>

      <Pagination
        page={page}
        pages={data?.pages ?? 1}
        total={data?.total ?? 0}
        onPage={(p) => { setPage(p); window.scrollTo(0, 0) }}
      />
    </div>
  )
}
