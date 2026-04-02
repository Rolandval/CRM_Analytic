import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Phone, Pencil, Check, X, Trash2, MessageSquare,
  PhoneCall,
} from 'lucide-react'
import { format } from 'date-fns'
import { usersApi } from '../api/users'
import { callsApi } from '../api/calls'
import { CallStateBadge } from '../components/calls/CallStateBadge'
import { CallTypeBadge } from '../components/calls/CallTypeBadge'
import { PageSpinner } from '../components/ui/Spinner'

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', category_id: '', type_ids: [] as number[] })
  const [deleteConfirm, setDeleteConfirm] = useState(false)

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', id],
    queryFn: () => usersApi.getById(Number(id)),
    enabled: !!id,
  })
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: usersApi.listCategories })
  const { data: types }      = useQuery({ queryKey: ['types'],      queryFn: usersApi.listTypes })
  const { data: callsData }  = useQuery({
    queryKey: ['user-calls', id],
    queryFn: () => callsApi.list({ user_id: Number(id), page: 1, page_size: 20 }),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (data: Parameters<typeof usersApi.update>[1]) => usersApi.update(Number(id), data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['user', id] })
      qc.invalidateQueries({ queryKey: ['users'] })
      setEditing(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => usersApi.delete(Number(id)),
    onSuccess: () => navigate('/users'),
  })

  const startEdit = () => {
    if (!user) return
    setForm({
      name: user.name ?? '',
      description: user.description ?? '',
      category_id: user.category ? String(user.category.id) : '',
      type_ids: user.types.map(t => t.id),
    })
    setEditing(true)
  }

  const saveEdit = () => {
    updateMutation.mutate({
      name: form.name || undefined,
      description: form.description || undefined,
      category_id: form.category_id ? Number(form.category_id) : undefined,
      type_ids: form.type_ids,
    })
  }

  if (isLoading) return <PageSpinner />
  if (!user) return <div className="text-slate-500 p-8">User not found</div>

  return (
    <div className="space-y-5 max-w-3xl animate-slide-up">

      {/* Back */}
      <Link to="/users"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors font-medium">
        <ArrowLeft size={14} />
        Back to clients
      </Link>

      {/* Profile card */}
      <div className="card overflow-hidden">

        {/* Gradient top bar */}
        <div className="h-1.5 w-full" style={{ background: 'linear-gradient(90deg, #6366f1, #8b5cf6, #3b82f6)' }} />

        {/* Header */}
        <div className="px-6 py-5 flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 text-white shadow-sm"
               style={{ background: 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)' }}>
            <Phone size={22} strokeWidth={2} />
          </div>
          <div className="flex-1 min-w-0">
            {editing ? (
              <input
                className="input text-base font-bold mb-1 h-10"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="Client name…"
              />
            ) : (
              <h1 className="text-xl font-bold text-slate-900 truncate">
                {user.name ?? <span className="text-slate-400 font-normal">Unnamed client</span>}
              </h1>
            )}
            <p className="text-sm text-slate-400 font-mono mt-0.5">{user.phone_number}</p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {editing ? (
              <>
                <button onClick={saveEdit} disabled={updateMutation.isPending} className="btn-primary h-9 px-4">
                  <Check size={14} strokeWidth={2.5} />
                  Save
                </button>
                <button onClick={() => setEditing(false)} className="btn-secondary h-9">
                  <X size={14} />
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button onClick={startEdit} className="btn-secondary h-9">
                  <Pencil size={13} />
                  Edit
                </button>
                {!deleteConfirm ? (
                  <button onClick={() => setDeleteConfirm(true)}
                    className="w-9 h-9 flex items-center justify-center rounded-xl text-slate-400
                               border border-black/[0.08] bg-white hover:bg-rose-50 hover:text-rose-500
                               hover:border-rose-200 transition-all shadow-card">
                    <Trash2 size={15} />
                  </button>
                ) : (
                  <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 rounded-xl px-3 py-2">
                    <span className="text-xs text-rose-700 font-medium">Delete?</span>
                    <button onClick={() => deleteMutation.mutate()} disabled={deleteMutation.isPending}
                      className="text-xs font-bold text-rose-600 hover:text-rose-800 transition-colors">Yes</button>
                    <button onClick={() => setDeleteConfirm(false)}
                      className="text-xs text-slate-400 hover:text-slate-600 transition-colors">No</button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-3 divide-x divide-black/[0.05] border-t border-black/[0.05]">
          <div className="px-6 py-4">
            <p className="section-title mb-1.5">Total Calls</p>
            <p className="text-2xl font-bold text-slate-900">{user.calls_count}</p>
          </div>
          <div className="px-6 py-4">
            <p className="section-title mb-1.5">Member Since</p>
            <p className="text-sm font-semibold text-slate-700 mt-0.5">
              {format(new Date(user.created_at), 'dd MMM yyyy')}
            </p>
          </div>
          <div className="px-6 py-4">
            <p className="section-title mb-1.5">Category</p>
            {editing ? (
              <select
                className="input h-8 text-sm mt-0.5"
                value={form.category_id}
                onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}
              >
                <option value="">None</option>
                {categories?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            ) : user.category ? (
              <span className="badge text-xs font-semibold mt-0.5"
                    style={{ background: 'rgba(99,102,241,0.10)', color: '#4338ca' }}>
                {user.category.name}
              </span>
            ) : (
              <span className="text-slate-300 text-sm">—</span>
            )}
          </div>
        </div>

        {/* Types */}
        <div className="px-6 py-4 border-t border-black/[0.04]">
          <p className="section-title mb-3">Types</p>
          {editing ? (
            <div className="flex flex-wrap gap-2">
              {types?.map(t => {
                const active = form.type_ids.includes(t.id)
                return (
                  <label key={t.id}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer border transition-all duration-150"
                    style={active
                      ? { background: 'rgba(99,102,241,0.12)', borderColor: 'rgba(99,102,241,0.3)', color: '#4338ca' }
                      : { background: 'white', borderColor: 'rgba(0,0,0,0.08)', color: '#64748b' }
                    }
                  >
                    <input type="checkbox" className="hidden"
                      checked={active}
                      onChange={e => setForm(f => ({
                        ...f,
                        type_ids: e.target.checked ? [...f.type_ids, t.id] : f.type_ids.filter(x => x !== t.id)
                      }))} />
                    {active && <Check size={11} strokeWidth={3} />}
                    {t.name}
                  </label>
                )
              })}
            </div>
          ) : user.types.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {user.types.map(t => (
                <span key={t.id} className="badge text-xs font-semibold"
                      style={{ background: 'rgba(139,92,246,0.10)', color: '#6d28d9' }}>
                  {t.name}
                </span>
              ))}
            </div>
          ) : (
            <span className="text-slate-300 text-sm">No types assigned</span>
          )}
        </div>

        {/* Notes */}
        <div className="px-6 py-4 border-t border-black/[0.04]">
          <p className="section-title mb-3">Notes</p>
          {editing ? (
            <textarea
              className="input resize-none text-sm"
              rows={3}
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Add notes about this client…"
            />
          ) : user.description ? (
            <p className="text-sm text-slate-600 leading-relaxed">{user.description}</p>
          ) : (
            <span className="text-slate-300 text-sm">No notes</span>
          )}
        </div>
      </div>

      {/* Recent calls */}
      <div className="card overflow-hidden">
        <div className="h-1 w-full" style={{ background: 'linear-gradient(90deg, #10b981, #059669)' }} />
        <div className="px-6 py-4 flex items-center justify-between border-b border-black/[0.05]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                 style={{ background: 'rgba(16,185,129,0.10)' }}>
              <PhoneCall size={14} className="text-emerald-600" strokeWidth={2.5} />
            </div>
            <h2 className="font-bold text-slate-900">Recent Calls</h2>
          </div>
          {callsData && callsData.total > 0 && (
            <span className="badge text-xs" style={{ background: 'rgba(0,0,0,0.05)', color: '#64748b' }}>
              {callsData.total} total
            </span>
          )}
        </div>
        <div>
          {callsData?.items.map(call => (
            <Link
              key={call.id}
              to={`/calls/${call.id}`}
              className="flex items-center gap-4 px-6 py-3.5 border-b border-black/[0.04]
                         hover:bg-brand-50/30 transition-colors group"
            >
              <CallTypeBadge type={call.call_type} />
              <CallStateBadge state={call.call_state} />
              <span className="text-xs text-slate-400 ml-auto font-medium">
                {call.date ? format(new Date(call.date), 'dd MMM, HH:mm') : '—'}
              </span>
              <span className="text-xs font-bold text-slate-500 w-14 text-right tabular-nums">
                {Math.round(call.seconds_talktime)}s
              </span>
            </Link>
          ))}
          {callsData?.items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-14 gap-3">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center"
                   style={{ background: 'rgba(0,0,0,0.04)' }}>
                <MessageSquare size={18} strokeWidth={1.5} className="text-slate-400" />
              </div>
              <p className="text-slate-400 text-sm font-medium">No calls recorded</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
