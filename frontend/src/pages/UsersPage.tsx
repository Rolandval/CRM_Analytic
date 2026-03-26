import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  Search, Phone, Users, SlidersHorizontal, ArrowUpDown,
  ArrowUp, ArrowDown, Pencil, Trash2, X, Check, Tag
} from 'lucide-react'
import { usersApi } from '../api/users'
import { Pagination } from '../components/ui/Pagination'
import { PageSpinner } from '../components/ui/Spinner'
import type { UserFilters } from '../api/types'

type SortField = 'id' | 'name' | 'phone_number' | 'calls_count' | 'created_at'

// ── Inline category/type editor modal ────────────────────────────────────────

function ManageModal({
  title,
  items,
  onAdd,
  onUpdate,
  onDelete,
  onClose,
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h3 className="font-semibold text-slate-800">{title}</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-slate-500">
            <X size={16} />
          </button>
        </div>

        <div className="p-6 space-y-3 max-h-80 overflow-y-auto">
          {items.map(item => (
            <div key={item.id} className="flex items-center gap-2 group">
              {editId === item.id ? (
                <>
                  <input
                    className="flex-1 px-3 py-1.5 text-sm border border-blue-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={editName}
                    onChange={e => setEditName(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSave(item.id)}
                    autoFocus
                  />
                  <button onClick={() => handleSave(item.id)} disabled={loading}
                    className="p-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors">
                    <Check size={14} />
                  </button>
                  <button onClick={() => setEditId(null)}
                    className="p-1.5 rounded-lg hover:bg-slate-100 transition-colors text-slate-400">
                    <X size={14} />
                  </button>
                </>
              ) : (
                <>
                  <span className="flex-1 text-sm text-slate-700 px-1">{item.name}</span>
                  <button onClick={() => { setEditId(item.id); setEditName(item.name) }}
                    className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-slate-100 transition-all text-slate-400">
                    <Pencil size={13} />
                  </button>
                  <button onClick={() => onDelete(item.id)} disabled={loading}
                    className="p-1.5 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-50 transition-all text-red-400">
                    <Trash2 size={13} />
                  </button>
                </>
              )}
            </div>
          ))}
          {items.length === 0 && (
            <p className="text-sm text-slate-400 text-center py-4">No items yet</p>
          )}
        </div>

        <div className="px-6 pb-5 pt-2 border-t border-slate-100">
          <div className="flex gap-2">
            <input
              className="flex-1 px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="New name…"
              value={newName}
              onChange={e => setNewName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAdd()}
            />
            <button onClick={handleAdd} disabled={loading || !newName.trim()}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-40">
              Add
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Sort header cell ──────────────────────────────────────────────────────────

function SortTh({
  field, label, current, order, onSort
}: {
  field: SortField, label: string, current: SortField, order: 'asc' | 'desc', onSort: (f: SortField) => void
}) {
  const active = current === field
  return (
    <th
      className="text-left px-5 py-3.5 cursor-pointer select-none group"
      onClick={() => onSort(field)}
    >
      <div className="flex items-center gap-1.5">
        <span className={`text-xs font-semibold uppercase tracking-wider transition-colors ${active ? 'text-blue-600' : 'text-slate-400 group-hover:text-slate-600'}`}>
          {label}
        </span>
        {active
          ? (order === 'desc' ? <ArrowDown size={12} className="text-blue-500" /> : <ArrowUp size={12} className="text-blue-500" />)
          : <ArrowUpDown size={11} className="text-slate-300 group-hover:text-slate-400 transition-colors" />
        }
      </div>
    </th>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

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
    page,
    page_size: 25,
    search: search || undefined,
    category_id: categoryId,
    type_id: typeId,
    has_analytics: hasAnalytics,
    sort_by: sortBy,
    sort_order: sortOrder,
  }

  const { data, isLoading } = useQuery({
    queryKey: ['users', filters],
    queryFn: () => usersApi.list(filters),
  })

  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: usersApi.listCategories })
  const { data: types } = useQuery({ queryKey: ['types'], queryFn: usersApi.listTypes })

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ['users'] })
    qc.invalidateQueries({ queryKey: ['categories'] })
    qc.invalidateQueries({ queryKey: ['types'] })
  }

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortOrder(o => o === 'desc' ? 'asc' : 'desc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
    setPage(1)
  }

  const resetFilters = () => {
    setSearch(''); setCategoryId(undefined); setTypeId(undefined); setHasAnalytics(undefined); setPage(1)
  }

  const hasActiveFilters = !!(search || categoryId || typeId || hasAnalytics !== undefined)

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 tracking-tight">Clients</h1>
          <p className="text-slate-400 text-sm mt-0.5">
            {data?.total !== undefined ? `${data.total.toLocaleString()} total` : '…'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setManageModal('categories')}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm"
          >
            <Tag size={14} />
            Categories
          </button>
          <button
            onClick={() => setManageModal('types')}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm text-slate-600 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm"
          >
            <Users size={14} />
            Types
          </button>
        </div>
      </div>

      {/* Search + filter bar */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              className="w-full pl-10 pr-4 py-2.5 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
              placeholder="Search by name or phone number…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1) }}
            />
          </div>
          <button
            onClick={() => setShowFilters(v => !v)}
            className={`inline-flex items-center gap-2 px-4 py-2.5 text-sm rounded-xl border transition-all ${
              showFilters || hasActiveFilters
                ? 'bg-blue-50 border-blue-200 text-blue-600'
                : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
            }`}
          >
            <SlidersHorizontal size={14} />
            Filters
            {hasActiveFilters && (
              <span className="w-5 h-5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center font-medium">
                {[categoryId, typeId, hasAnalytics !== undefined].filter(Boolean).length}
              </span>
            )}
          </button>
        </div>

        {showFilters && (
          <div className="flex flex-wrap gap-3 pt-1">
            <select
              className="px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-40"
              value={categoryId ?? ''}
              onChange={e => { setCategoryId(e.target.value ? Number(e.target.value) : undefined); setPage(1) }}
            >
              <option value="">All categories</option>
              {categories?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>

            <select
              className="px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-36"
              value={typeId ?? ''}
              onChange={e => { setTypeId(e.target.value ? Number(e.target.value) : undefined); setPage(1) }}
            >
              <option value="">All types</option>
              {types?.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>

            <select
              className="px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-40"
              value={hasAnalytics === undefined ? '' : String(hasAnalytics)}
              onChange={e => { setHasAnalytics(e.target.value === '' ? undefined : e.target.value === 'true'); setPage(1) }}
            >
              <option value="">All clients</option>
              <option value="true">With AI analytics</option>
              <option value="false">Without AI analytics</option>
            </select>

            {hasActiveFilters && (
              <button onClick={resetFilters}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors">
                <X size={13} />
                Clear
              </button>
            )}
          </div>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <PageSpinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <SortTh field="phone_number" label="Phone" current={sortBy} order={sortOrder} onSort={handleSort} />
                  <SortTh field="name" label="Name" current={sortBy} order={sortOrder} onSort={handleSort} />
                  <th className="text-left px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-slate-400">Category</th>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold uppercase tracking-wider text-slate-400">Types</th>
                  <SortTh field="calls_count" label="Calls" current={sortBy} order={sortOrder} onSort={handleSort} />
                </tr>
              </thead>
              <tbody>
                {data?.items.map(user => (
                  <tr
                    key={user.id}
                    className="border-b border-slate-50 hover:bg-blue-50/40 cursor-pointer transition-colors group"
                    onClick={() => navigate(`/users/${user.id}`)}
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-slate-100 to-slate-200 rounded-full flex items-center justify-center flex-shrink-0 group-hover:from-blue-100 group-hover:to-blue-200 transition-all">
                          <Phone size={13} className="text-slate-500 group-hover:text-blue-500 transition-colors" />
                        </div>
                        <span className="font-mono text-sm text-slate-700">{user.phone_number ?? <span className="text-slate-300">—</span>}</span>
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-sm font-medium text-slate-700">
                        {user.name ?? <span className="text-slate-300 font-normal">Unnamed</span>}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      {user.category
                        ? <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">{user.category.name}</span>
                        : <span className="text-slate-300 text-sm">—</span>
                      }
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-1">
                        {user.types.length > 0
                          ? user.types.map(t => (
                              <span key={t.id} className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                                {t.name}
                              </span>
                            ))
                          : <span className="text-slate-300 text-sm">—</span>
                        }
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-sm font-semibold text-slate-700">{user.calls_count}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {data?.items.length === 0 && (
              <div className="text-center py-16">
                <Users size={32} className="mx-auto text-slate-200 mb-3" />
                <p className="text-slate-400 text-sm">No clients found</p>
                {hasActiveFilters && (
                  <button onClick={resetFilters} className="mt-2 text-sm text-blue-500 hover:underline">
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

      {/* Categories modal */}
      {manageModal === 'categories' && categories && (
        <ManageModal
          title="Manage Categories"
          items={categories}
          onAdd={async name => { await usersApi.createCategory(name); invalidate() }}
          onUpdate={async (id, name) => { await usersApi.updateCategory(id, name); invalidate() }}
          onDelete={async id => { await usersApi.deleteCategory(id); invalidate() }}
          onClose={() => setManageModal(null)}
        />
      )}

      {/* Types modal */}
      {manageModal === 'types' && types && (
        <ManageModal
          title="Manage Types"
          items={types}
          onAdd={async name => { await usersApi.createType(name); invalidate() }}
          onUpdate={async (id, name) => { await usersApi.updateType(id, name); invalidate() }}
          onDelete={async id => { await usersApi.deleteType(id); invalidate() }}
          onClose={() => setManageModal(null)}
        />
      )}
    </div>
  )
}
