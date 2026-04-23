import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Search, SlidersHorizontal, X, Phone,
  ExternalLink, Copy, ChevronDown,
} from 'lucide-react'
import { format } from 'date-fns'
import { callsApi } from '../api/calls'
import type { CallFilters, CallState, CallType } from '../api/types'
import { CallStateBadge } from '../components/calls/CallStateBadge'
import { CallTypeBadge } from '../components/calls/CallTypeBadge'
import { Pagination } from '../components/ui/Pagination'
import { PageSpinner } from '../components/ui/Spinner'
import { ExportMenu, downloadBlob } from '../components/ui/ExportMenu'

const STATES: { value: CallState; label: string }[] = [
  { value: 'ANSWER',   label: 'Answered' },
  { value: 'NOANSWER', label: 'No Answer' },
  { value: 'BUSY',     label: 'Busy' },
  { value: 'FAILED',   label: 'Failed' },
]
const TYPES: { value: CallType; label: string }[] = [
  { value: 'IN',  label: 'Inbound' },
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
  const [copiedId, setCopiedId] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['calls', page, filters, search],
    queryFn: () => callsApi.list({ ...filters, search: search || undefined, page, page_size: 25 }),
  })

  const setFilter = (k: keyof typeof filters, v: unknown) => {
    setFilters(f => ({ ...f, [k]: v || undefined }))
    setPage(1)
  }

  const clearAll = () => { setFilters({}); setSearch(''); setPage(1) }
  const activeCount = Object.values(filters).filter(Boolean).length + (search ? 1 : 0)

  const copyNumber = (e: React.MouseEvent, num: string, id: number) => {
    e.stopPropagation()
    navigator.clipboard.writeText(num).catch(() => {})
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 1500)
  }

  return (
    <div className="space-y-5 animate-slide-up">

      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gradient">Calls</h1>
          <p className="text-slate-500 text-sm mt-1">
            {data?.total != null ? `${data.total.toLocaleString()} calls in total` : 'Loading…'}
          </p>
        </div>
        <ExportMenu
          recordCount={data?.total}
          onExport={async format => {
            const { blob, filename } = await callsApi.export(format, {
              ...filters,
              search: search || undefined,
            })
            downloadBlob(blob, filename)
          }}
        />
      </div>

      {/* Search + filter toolbar */}
      <div className="card p-3.5 flex flex-wrap items-center gap-2.5">
        <div className="relative flex-1 min-w-52">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            className="input pl-10 h-10 text-sm"
            placeholder="Search by phone number…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
        </div>

        <button
          className={`btn-secondary h-10 gap-2 ${showFilters ? 'ring-2 ring-brand-500/20 border-brand-300 text-brand-600' : ''}`}
          onClick={() => setShowFilters(v => !v)}
        >
          <SlidersHorizontal size={14} />
          Filters
          {activeCount > 0 && (
            <span
              className="w-5 h-5 text-white text-[10px] rounded-full flex items-center justify-center font-bold"
              style={{ background: 'linear-gradient(135deg, #6366f1, #3b82f6)' }}
            >
              {activeCount}
            </span>
          )}
          <ChevronDown size={13} className={`transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </button>

        {activeCount > 0 && (
          <button className="btn-ghost h-10 text-rose-500 hover:bg-rose-50 hover:text-rose-600" onClick={clearAll}>
            <X size={14} />
            Clear all
          </button>
        )}
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="card p-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 animate-slide-up">
          {[
            { label: 'State', content: (
              <select className="input h-9 text-sm" value={filters.call_state ?? ''}
                onChange={e => setFilter('call_state', e.target.value as CallState)}>
                <option value="">All states</option>
                {STATES.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            )},
            { label: 'Type', content: (
              <select className="input h-9 text-sm" value={filters.call_type ?? ''}
                onChange={e => setFilter('call_type', e.target.value as CallType)}>
                <option value="">All types</option>
                {TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            )},
            { label: 'Date from', content: (
              <input type="datetime-local" className="input h-9 text-sm"
                value={filters.date_from ?? ''} onChange={e => setFilter('date_from', e.target.value)} />
            )},
            { label: 'Date to', content: (
              <input type="datetime-local" className="input h-9 text-sm"
                value={filters.date_to ?? ''} onChange={e => setFilter('date_to', e.target.value)} />
            )},
            { label: 'Min dur (s)', content: (
              <input type="number" min={0} className="input h-9 text-sm"
                value={filters.min_duration ?? ''}
                onChange={e => setFilter('min_duration', e.target.value ? Number(e.target.value) : undefined)} />
            )},
            { label: 'Max dur (s)', content: (
              <input type="number" min={0} className="input h-9 text-sm"
                value={filters.max_duration ?? ''}
                onChange={e => setFilter('max_duration', e.target.value ? Number(e.target.value) : undefined)} />
            )},
          ].map(({ label, content }) => (
            <div key={label}>
              <label className="section-title mb-1.5 block">{label}</label>
              {content}
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="py-14 flex items-center justify-center">
            <PageSpinner />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ background: 'linear-gradient(90deg, #f8f9fc 0%, #f1f3f8 100%)' }}
                    className="border-b border-black/[0.05]">
                  <th className="th">#</th>
                  <th className="th">Type</th>
                  <th className="th">State</th>
                  <th className="th">From</th>
                  <th className="th">To</th>
                  <th className="th">Date</th>
                  <th className="th">Duration</th>
                  <th className="th">Recording</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map(call => (
                  <tr
                    key={call.id}
                    className="tr"
                    onClick={() => navigate(`/calls/${call.id}`)}
                  >
                    <td className="td">
                      <span className="font-mono text-xs text-slate-400 font-medium">#{call.id}</span>
                    </td>
                    <td className="td">
                      <CallTypeBadge type={call.call_type} />
                    </td>
                    <td className="td">
                      <CallStateBadge state={call.call_state} />
                    </td>
                    <td className="td">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-slate-700 font-medium">
                          {call.from_number ?? <span className="text-slate-300">—</span>}
                        </span>
                        {call.from_number && (
                          <button
                            className="opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center
                                       rounded-lg text-slate-400 hover:text-slate-600 hover:bg-black/[0.06] transition-all"
                            onClick={e => copyNumber(e, call.from_number!, call.id)}
                            title="Copy"
                          >
                            {copiedId === call.id
                              ? <span className="text-emerald-500 text-[10px] font-bold">✓</span>
                              : <Copy size={11} />
                            }
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="td">
                      <span className="font-mono text-xs text-slate-700 font-medium">
                        {call.to_number ?? <span className="text-slate-300">—</span>}
                      </span>
                    </td>
                    <td className="td">
                      <span className="text-slate-500 text-xs font-medium">
                        {call.date ? format(new Date(call.date), 'dd MMM yyyy, HH:mm') : '—'}
                      </span>
                    </td>
                    <td className="td">
                      <span className="font-semibold text-slate-700 tabular-nums text-xs">
                        {formatDuration(call.seconds_talktime)}
                      </span>
                    </td>
                    <td className="td">
                      {call.mp3_link ? (
                        <a
                          href={call.mp3_link}
                          target="_blank" rel="noreferrer"
                          onClick={e => e.stopPropagation()}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all
                                     hover:opacity-80"
                          style={{ background: 'rgba(99,102,241,0.10)', color: '#4338ca' }}
                        >
                          <Phone size={10} strokeWidth={2.5} />
                          MP3
                          <ExternalLink size={9} />
                        </a>
                      ) : (
                        <span className="text-slate-300 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {data?.items.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 gap-4">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                     style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(59,130,246,0.08))' }}>
                  <Phone size={24} strokeWidth={1.5} className="text-brand-500" />
                </div>
                <div className="text-center">
                  <p className="text-slate-700 font-semibold">No calls found</p>
                  <p className="text-slate-400 text-sm mt-1">Try adjusting your filters</p>
                </div>
                {activeCount > 0 && (
                  <button onClick={clearAll} className="btn-secondary text-sm">
                    Clear filters
                  </button>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      <Pagination
        page={page}
        pages={data?.pages ?? 1}
        total={data?.total ?? 0}
        onPage={p => { setPage(p); window.scrollTo(0, 0) }}
      />
    </div>
  )
}
