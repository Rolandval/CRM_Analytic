import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Search, Phone } from 'lucide-react'
import { usersApi } from '../api/users'
import { Pagination } from '../components/ui/Pagination'
import { PageSpinner } from '../components/ui/Spinner'

export default function UsersPage() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState<number | undefined>()

  const { data, isLoading } = useQuery({
    queryKey: ['users', page, search, categoryId],
    queryFn: () => usersApi.list({ page, page_size: 25, search: search || undefined, category_id: categoryId }),
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: usersApi.listCategories,
  })

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold">Users</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          {data?.total.toLocaleString() ?? '…'} users total
        </p>
      </div>

      {/* Filters */}
      <div className="card p-3 flex flex-wrap gap-2">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
          <input
            className="input pl-8"
            placeholder="Search by name or number…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
        <select
          className="input w-44"
          value={categoryId ?? ''}
          onChange={e => setCategoryId(e.target.value ? Number(e.target.value) : undefined)}
        >
          <option value="">All categories</option>
          {categories?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {isLoading ? <PageSpinner /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-700 text-xs text-slate-500 uppercase tracking-wider">
                  <th className="text-left px-4 py-3">Phone</th>
                  <th className="text-left px-4 py-3">Name</th>
                  <th className="text-left px-4 py-3">Category</th>
                  <th className="text-left px-4 py-3">Calls</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {data?.items.map(user => (
                  <tr
                    key={user.id}
                    className="hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/users/${user.id}`)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center">
                          <Phone size={12} className="text-slate-500" />
                        </div>
                        <span className="font-mono">{user.phone_number ?? '—'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">{user.name ?? <span className="text-slate-400">Unnamed</span>}</td>
                    <td className="px-4 py-3">
                      {user.category
                        ? <span className="badge bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-300">{user.category.name}</span>
                        : <span className="text-slate-400">—</span>
                      }
                    </td>
                    <td className="px-4 py-3 font-semibold">{user.calls_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {data?.items.length === 0 && (
              <div className="text-center py-12 text-slate-400">No users found</div>
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
