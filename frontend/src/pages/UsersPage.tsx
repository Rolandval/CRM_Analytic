import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Search, Phone, Users, SlidersHorizontal, ArrowUpDown,
  ArrowUp, ArrowDown, Pencil, Trash2, X, Check, Tag,
  ChevronDown,
} from 'lucide-react'
import { usersApi } from '../api/users'
import { Pagination } from '../components/ui/Pagination'
import { PageSpinner } from '../components/ui/Spinner'
import { ExportMenu, downloadBlob } from '../components/ui/ExportMenu'
import type { UserFilters } from '../api/types'

type SortField = 'id' | 'name' | 'phone_number' | 'calls_count' | 'created_at'

// ── Manage Modal ────────────────────────────────────────────────────────────

function ManageModal({
  title, items, onAdd, onUpdate, onDelete, onClose,
}: {
  title: string
  items: { id: number; name: string }[]
  onAdd: (name: string) => Promise<void>
  onUpdate: (id: number, name: string) => Promise<void>
  onDelete: (id: number) => Promise<void>
  onClose: () => void
}) {
  const [newName, setNewName] = useState('')
  const [editId, setEditId] = useState<number | null>(null)
  const [editName, setEditName] = useState('')
  const [loading, setLoading] = useState(false)

  const handleAdd = async () => {
    if (!newName.trim()) return
    setLoading(true)
    try { await onAdd(newName.trim()); setNewName('') } finally { setLoading(false) }
  }

  const handleSave = async (id: number) => {
    if (!editName.trim()) return
    setLoading(true)
    try { await onUpdate(id, editName.trim()); setEditId(null) } finally { setLoading(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl shadow-popover w-full max-w-md mx-4 overflow-hidden animate-scale-in">

        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5">
          <h3 className="font-bold text-slate-900 text-base">{title}</h3>
          <button onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-xl text-slate-400
                       hover:text-slate-600 hover:bg-black/[0.06] transition-all">
            <X size={15} />
          </button>
        </div>

        <div className="h-px bg-black/[0.06] mx-6" />

        {/* List */}
        <div className="p-4 space-y-1.5 max-h-72 overflow-y-auto">
          {items.map(item => (
            <div key={item.id}
              className="flex items-center gap-2 px-2 py-2 rounded-xl hover:bg-slate-50 group transition-colors">
              {editId === item.id ? (
                <>
                  <input
                    className="flex-1 px-3 py-1.5 text-sm border border-brand-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500/30 bg-brand-50/30"
                    value={editName}
                    onChange={e => setEditName(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSave(item.id)}
                    autoFocus
                  />
                  <button onClick={() => handleSave(item.id)} disabled={loading}
                    className="w-7 h-7 flex items-center justify-center rounded-lg text-white transition-all hover:opacity-90"
                    style={{ background: 'linear-gradient(135deg, #6366f1, #3b82f6)' }}>
                    <Check size={13} strokeWidth={2.5} />
                  </button>
                  <button onClick={() => setEditId(null)}
                    className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:bg-black/[0.06] transition-all">
                    <X size={13} />
                  </button>
                </>
              ) : (
                <>
                  <div className="w-2 h-2 rounded-full bg-brand-500/30 flex-shrink-0 ml-1" />
                  <span className="flex-1 text-sm text-slate-700 font-medium">{item.name}</span>
                  <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity">
                    <button onClick={() => { setEditId(item.id); setEditName(item.name) }}
                      className="w-7 h-7 flex items-center justify-center rounded-lg text-slate-400 hover:bg-black/[0.06] hover:text-slate-600 transition-all">
                      <Pencil size={12} />
                    </button>
                    <button onClick={() => onDelete(item.id)} disabled={loading}
                      className="w-7 h-7 flex items-center justify-center rounded-lg text-rose-400 hover:bg-rose-50 hover:text-rose-600 transition-all">
                      <Trash2 size={12} />
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
          {items.length === 0 && (
            <p className="text-sm text-slate-400 text-center py-6">No items yet</p>
          )}
        </div>

        {/* Add new */}
        <div className="px-5 pb-5 pt-3">
          <div className="flex gap-2">
            <input
              className="input flex-1 h-10 text-sm"
              placeholder="Add new…"
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAdd()}
            />
            <button
              onClick={handleAdd}
              disabled={loading || !newName.trim()}
              className="btn-primary h-10 px-5"
            >
              Add
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sort header ─────────────────────────────────────────────────────────────

function SortTh({ field, label, current, order, onSort }: {
  field: SortField; label: string; current: SortField; order: 'asc' | 'desc'; onSort: (f: SortField) => void
}) {
  const active = current === field
  return (
    <th className="th cursor-pointer select-none group" onClick={() => onSort(field)}>
      <div className="flex items-center gap-1.5">
        <span className={`transition-colors ${active ? 'text-brand-600' : 'group-hover:text-slate-600'}`}>
          {label}
        </span>
        {active
          ? (order === 'desc'
              ? <ArrowDown size={11} className="text-brand-500" />
              : <ArrowUp size={11} className="text-brand-500" />)
          : <ArrowUpDown size={10} className="text-slate-300 group-hover:text-slate-400 transition-colors" />
        }
      </div>
    </th>
  )
}

// ── Page ────────────────────────────────────────────────────────────────────

export default function UsersPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState<number | undefined>()
  const [typeId, setTypeId] = useState<number | undefined>()
  const [hasAnalytics, setHasAnalytics] = useState<boolean | undefined>()
  const [sortBy, setSortBy] = useState<SortField>('id')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [showFilters, setShowFilters] = useState(false)
  const [manageModal, setManageModal] = useState<'categories' | 'types' | null>(null)

  const filters: UserFilters = {
    page, page_size: 25,
    search: search || undefined,
    category_id: categoryId,
    type_id: typeId,
    has_analytics: hasAnalytics,
    sort_by: sortBy,
    sort_order: sortOrder,
  }

  const { data, isLoading } = useQuery({ queryKey: ['users', filters], queryFn: () => usersApi.list(filters) })
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: usersApi.listCategories })
  const { data: types } = useQuery({ queryKey: ['types'], queryFn: usersApi.listTypes })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['users'] })
    qc.invalidateQueries({ queryKey: ['categories'] })
    qc.invalidateQueries({ queryKey: ['types'] })
  }

  const handleSort = (field: SortField) => {
    if (sortBy === field) setSortOrder(o => o === 'desc' ? 'asc' : 'desc')
    else { setSortBy(field); setSortOrder('desc') }
    setPage(1)
  }

  const resetFilters = () => {
    setSearch(''); setCategoryId(undefined); setTypeId(undefined); setHasAnalytics(undefined); setPage(1)
  }

  const hasActiveFilters = !!(search || categoryId || typeId || hasAnalytics !== undefined)
  const activeCount = [categoryId, typeId, hasAnalytics !== undefined ? 1 : null].filter(Boolean).length + (search ? 1 : 0)

  return (
    <div className="space-y-5 animate-slide-up">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gradient">Clients</h1>
          <p className="text-slate-500 text-sm mt-1">
            {data?.total !== undefined ? `${data.total.toLocaleString()} total clients` : '…'}
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button onClick={() => setManageModal('categories')} className="btn-secondary text-sm">
            <Tag size={14} />
            Categories
          </button>
          <button onClick={() => setManageModal('types')} className="btn-secondary text-sm">
            <Users size={14} />
            Types
          </button>
          <ExportMenu
            recordCount={data?.total}
            onExport={async format => {
              const { blob, filename } = await usersApi.export(format, {
                search: search || undefined,
                category_id: categoryId,
                type_id: typeId,
                has_analytics: hasAnalytics,
                sort_by: sortBy,
                sort_order: sortOrder,
              })
              downloadBlob(blob, filename)
            }}
          />
        </div>
      </div>

      {/* Search + filters */}
      <div className="card p-3.5 flex flex-wrap items-center gap-2.5">
        <div className="relative flex-1 min-w-52">
          <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            className="input pl-10 h-10 text-sm"
            placeholder="Search by name or phone…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
        </div>

        <button
          className={`btn-secondary h-10 gap-2 ${showFilters ? 'ring-2 ring-brand-500/20 border-brand-300' : ''}`}
          onClick={() => setShowFilters(v => !v)}
        >
          <SlidersHorizontal size={14} />
          Filters
          {activeCount > 0 && (
            <span className="w-5 h-5 text-white text-[10px] rounded-full flex items-center justify-center font-bold"
                  style={{ background: 'linear-gradient(135deg, #6366f1, #3b82f6)' }}>
              {activeCount}
            </span>
          )}
          <ChevronDown size={13} className={`transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </button>

        {hasActiveFilters && (
          <button className="btn-ghost h-10 text-rose-500 hover:bg-rose-50 hover:text-rose-600" onClick={resetFilters}>
            <X size={14} /> Clear
          </button>
        )}
      </div>

      {/* Filter panel */}
      {showFilters && (
        <div className="card p-4 flex flex-wrap gap-3 animate-slide-up">
          <div className="min-w-44">
            <label className="section-title mb-1.5 block">Category</label>
            <select className="input h-9 text-sm" value={categoryId ?? ''}
              onChange={e => { setCategoryId(e.target.value ? Number(e.target.value) : undefined); setPage(1) }}>
              <option value="">All categories</option>
              {categories?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="min-w-36">
            <label className="section-title mb-1.5 block">Type</label>
            <select className="input h-9 text-sm" value={typeId ?? ''}
              onChange={e => { setTypeId(e.target.value ? Number(e.target.value) : undefined); setPage(1) }}>
              <option value="">All types</option>
              {types?.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div className="min-w-44">
            <label className="section-title mb-1.5 block">AI Analytics</label>
            <select className="input h-9 text-sm"
              value={hasAnalytics === undefined ? '' : String(hasAnalytics)}
              onChange={e => { setHasAnalytics(e.target.value === '' ? undefined : e.target.value === 'true'); setPage(1) }}>
              <option value="">All clients</option>
              <option value="true">With analytics</option>
              <option value="false">Without analytics</option>
            </select>
          </div>
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
            <table className="w-full">
              <thead>
                <tr style={{ background: 'linear-gradient(90deg, #f8f9fc 0%, #f1f3f8 100%)' }}
                    className="border-b border-black/[0.05]">
                  <SortTh field="phone_number" label="Phone"  current={sortBy} order={sortOrder} onSort={handleSort} />
                  <SortTh field="name"         label="Name"   current={sortBy} order={sortOrder} onSort={handleSort} />
                  <th className="th">Category</th>
                  <th className="th">Types</th>
                  <SortTh field="calls_count"  label="Calls"  current={sortBy} order={sortOrder} onSort={handleSort} />
                </tr>
              </thead>
              <tbody>
                {data?.items.map(user => (
                  <tr
                    key={user.id}
                    className="tr"
                    onClick={() => navigate(`/users/${user.id}`)}
                  >
                    <td className="td">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 group-hover:shadow-sm transition-all"
                          style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.12), rgba(59,130,246,0.12))' }}
                        >
                          <Phone size={13} strokeWidth={2} className="text-brand-600" />
                        </div>
                        <span className="font-mono text-xs text-slate-700 font-medium">
                          {user.phone_number ?? <span className="text-slate-300">—</span>}
                        </span>
                      </div>
                    </td>
                    <td className="td">
                      <span className="text-sm font-semibold text-slate-800">
                        {user.name ?? <span className="text-slate-300 font-normal text-xs">Unnamed</span>}
                      </span>
                    </td>
                    <td className="td">
                      {user.category ? (
                        <span className="badge text-xs font-semibold"
                              style={{ background: 'rgba(99,102,241,0.10)', color: '#4338ca' }}>
                          {user.category.name}
                        </span>
                      ) : (
                        <span className="text-slate-300 text-sm">—</span>
                      )}
                    </td>
                    <td className="td">
                      <div className="flex flex-wrap gap-1">
                        {user.types.length > 0 ? (
                          user.types.map(t => (
                            <span key={t.id}
                              className="inline-flex px-2 py-0.5 rounded-lg text-xs font-medium"
                              style={{ background: 'rgba(139,92,246,0.10)', color: '#6d28d9' }}>
                              {t.name}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-300 text-sm">—</span>
                        )}
                      </div>
                    </td>
                    <td className="td">
                      <span
                        className="inline-flex px-2.5 py-1 rounded-lg text-xs font-bold"
                        style={{ background: 'rgba(0,0,0,0.04)', color: '#475569' }}
                      >
                        {user.calls_count}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {data?.items.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 gap-4">
                <div className="w-16 h-16 rounded-2xl flex items-center justify-center"
                     style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.08), rgba(59,130,246,0.08))' }}>
                  <Users size={24} strokeWidth={1.5} className="text-brand-500" />
                </div>
                <div className="text-center">
                  <p className="text-slate-700 font-semibold">No clients found</p>
                  <p className="text-slate-400 text-sm mt-1">Try changing the search or filters</p>
                </div>
                {hasActiveFilters && (
                  <button onClick={resetFilters} className="btn-secondary text-sm">
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

      {manageModal === 'categories' && categories && (
        <ManageModal title="Manage Categories" items={categories}
          onAdd={async n => { await usersApi.createCategory(n); invalidate() }}
          onUpdate={async (id, n) => { await usersApi.updateCategory(id, n); invalidate() }}
          onDelete={async id => { await usersApi.deleteCategory(id); invalidate() }}
          onClose={() => setManageModal(null)} />
      )}

      {manageModal === 'types' && types && (
        <ManageModal title="Manage Types" items={types}
          onAdd={async n => { await usersApi.createType(n); invalidate() }}
          onUpdate={async (id, n) => { await usersApi.updateType(id, n); invalidate() }}
          onDelete={async id => { await usersApi.deleteType(id); invalidate() }}
          onClose={() => setManageModal(null)} />
      )}
    </div>
  )
}
