import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams, Link, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Phone, Pencil, Check, X, Trash2, MessageSquare
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
  const { data: types } = useQuery({ queryKey: ['types'], queryFn: usersApi.listTypes })

  const { data: callsData } = useQuery({
    queryKey: ['user-calls', id],
    queryFn: () => callsApi.list({ user_id: Number(id), page: 1, page_size: 20 }),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (data: Parameters<typeof usersApi.update>[1]) =>
      usersApi.update(Number(id), data),
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
    <div className="space-y-6 max-w-3xl">
      {/* Back */}
      <Link to="/users" className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 transition-colors">
        <ArrowLeft size={14} />
        Back to clients
      </Link>

      {/* Profile card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-5 flex items-center gap-4 border-b border-slate-100">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center flex-shrink-0">
            <Phone size={20} className="text-blue-600" />
          </div>
          <div className="flex-1 min-w-0">
            {editing ? (
              <input
                className="w-full text-lg font-semibold bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-1"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                placeholder="Name…"
              />
            ) : (
              <h1 className="text-xl font-bold text-slate-800 truncate">
                {user.name ?? <span className="text-slate-400 font-normal">Unnamed client</span>}
              </h1>
            )}
            <p className="text-sm text-slate-400 font-mono">{user.phone_number}</p>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            {editing ? (
              <>
                <button
                  onClick={saveEdit}
                  disabled={updateMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm rounded-xl font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  <Check size={14} />
                  Save
                </button>
                <button
                  onClick={() => setEditing(false)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-slate-600 text-sm rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors"
                >
                  <X size={14} />
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={startEdit}
                  className="inline-flex items-center gap-1.5 px-3 py-2 text-slate-600 text-sm rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors"
                >
                  <Pencil size={13} />
                  Edit
                </button>
                {!deleteConfirm ? (
                  <button
                    onClick={() => setDeleteConfirm(true)}
                    className="p-2 text-slate-400 rounded-xl border border-slate-200 hover:bg-red-50 hover:text-red-500 hover:border-red-200 transition-colors"
                  >
                    <Trash2 size={15} />
                  </button>
                ) : (
                  <div className="flex items-center gap-2 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
                    <span className="text-sm text-red-700">Delete?</span>
                    <button
                      onClick={() => deleteMutation.mutate()}
                      disabled={deleteMutation.isPending}
                      className="text-sm font-medium text-red-600 hover:text-red-700"
                    >
                      Yes
                    </button>
                    <button onClick={() => setDeleteConfirm(false)} className="text-sm text-slate-500 hover:text-slate-700">
                      No
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 divide-x divide-slate-100">
          <div className="px-6 py-4">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Total Calls</p>
            <p className="text-2xl font-bold text-slate-800">{user.calls_count}</p>
          </div>
          <div className="px-6 py-4">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Member Since</p>
            <p className="text-sm font-semibold text-slate-700 mt-1">{format(new Date(user.created_at), 'dd MMM yyyy')}</p>
          </div>
          <div className="px-6 py-4">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Category</p>
            {editing ? (
              <select
                className="mt-1 w-full text-sm bg-slate-50 border border-slate-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={form.category_id}
                onChange={e => setForm(f => ({ ...f, category_id: e.target.value }))}
              >
                <option value="">None</option>
                {categories?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            ) : user.category ? (
              <span className="mt-1 inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                {user.category.name}
              </span>
            ) : (
              <span className="text-sm text-slate-300">—</span>
            )}
          </div>
        </div>

        {/* Types */}
        <div className="px-6 py-4 border-t border-slate-100">
          <p className="text-xs text-slate-400 uppercase tracking-wider mb-2.5">Types</p>
          {editing ? (
            <div className="flex flex-wrap gap-2">
              {types?.map(t => (
                <label key={t.id}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium cursor-pointer border transition-all ${
                    form.type_ids.includes(t.id)
                      ? 'bg-blue-50 text-blue-700 border-blue-200'
                      : 'bg-slate-50 text-slate-500 border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={form.type_ids.includes(t.id)}
                    onChange={e => setForm(f => ({
                      ...f,
                      type_ids: e.target.checked
                        ? [...f.type_ids, t.id]
                        : f.type_ids.filter(x => x !== t.id)
                    }))}
                  />
                  {form.type_ids.includes(t.id) && <Check size={11} />}
                  {t.name}
                </label>
              ))}
            </div>
          ) : user.types.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {user.types.map(t => (
                <span key={t.id} className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                  {t.name}
                </span>
              ))}
            </div>
          ) : (
            <span className="text-sm text-slate-300">No types assigned</span>
          )}
        </div>

        {/* Description */}
        <div className="px-6 py-4 border-t border-slate-100">
          <p className="text-xs text-slate-400 uppercase tracking-wider mb-2.5">Notes</p>
          {editing ? (
            <textarea
              className="w-full text-sm bg-slate-50 border border-slate-200 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              rows={3}
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Add notes about this client…"
            />
          ) : user.description ? (
            <p className="text-sm text-slate-600 leading-relaxed">{user.description}</p>
          ) : (
            <span className="text-sm text-slate-300">No notes</span>
          )}
        </div>
      </div>

      {/* Recent calls */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="font-semibold text-slate-800">Recent Calls</h2>
          {callsData && callsData.total > 0 && (
            <span className="text-xs text-slate-400">{callsData.total} total</span>
          )}
        </div>
        <div>
          {callsData?.items.map(call => (
            <Link
              key={call.id}
              to={`/calls/${call.id}`}
              className="flex items-center gap-4 px-6 py-3.5 border-b border-slate-50 hover:bg-blue-50/30 transition-colors"
            >
              <CallTypeBadge type={call.call_type} />
              <CallStateBadge state={call.call_state} />
              <span className="text-sm text-slate-500 ml-auto">
                {call.date ? format(new Date(call.date), 'dd MMM HH:mm') : '—'}
              </span>
              <span className="text-sm font-mono text-slate-400 w-16 text-right">
                {Math.round(call.seconds_talktime)}s
              </span>
            </Link>
          ))}
          {callsData?.items.length === 0 && (
            <div className="text-center py-12">
              <MessageSquare size={28} className="mx-auto text-slate-200 mb-2" />
              <p className="text-slate-400 text-sm">No calls recorded</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
