import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Phone } from 'lucide-react'
import { format } from 'date-fns'
import { usersApi } from '../api/users'
import { callsApi } from '../api/calls'
import { CallStateBadge } from '../components/calls/CallStateBadge'
import { CallTypeBadge } from '../components/calls/CallTypeBadge'
import { PageSpinner } from '../components/ui/Spinner'

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>()

  const { data: user, isLoading } = useQuery({
    queryKey: ['user', id],
    queryFn: () => usersApi.getById(Number(id)),
    enabled: !!id,
  })

  const { data: callsData } = useQuery({
    queryKey: ['user-calls', id],
    queryFn: () => callsApi.list({ user_id: Number(id), page: 1, page_size: 20 }),
    enabled: !!id,
  })

  if (isLoading) return <PageSpinner />
  if (!user) return <div className="text-slate-500 p-8">User not found</div>

  return (
    <div className="space-y-5 max-w-3xl">
      <Link to="/users" className="btn-ghost text-sm w-fit">
        <ArrowLeft size={14} /> Back to users
      </Link>

      {/* Profile card */}
      <div className="card p-6">
        <div className="flex items-center gap-4 mb-5">
          <div className="w-14 h-14 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center">
            <Phone size={24} className="text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold">{user.name ?? 'Unnamed user'}</h1>
            <p className="text-sm text-slate-500 font-mono">{user.phone_number}</p>
          </div>
          {user.category && (
            <span className="ml-auto badge bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
              {user.category.name}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
            <p className="text-slate-500 mb-1">Total Calls</p>
            <p className="text-xl font-bold">{user.calls_count}</p>
          </div>
          <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
            <p className="text-slate-500 mb-1">Member since</p>
            <p className="font-medium">{format(new Date(user.created_at), 'dd MMM yyyy')}</p>
          </div>
          {user.types.length > 0 && (
            <div className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
              <p className="text-slate-500 mb-2">Types</p>
              <div className="flex flex-wrap gap-1">
                {user.types.map(t => (
                  <span key={t.id} className="badge bg-slate-200 text-slate-600 dark:bg-slate-600 dark:text-slate-200">
                    {t.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {user.description && (
          <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">{user.description}</p>
        )}
      </div>

      {/* Recent calls */}
      <div className="card overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700">
          <h2 className="font-semibold">Recent Calls</h2>
        </div>
        <div className="divide-y divide-slate-100 dark:divide-slate-700">
          {callsData?.items.map(call => (
            <Link
              key={call.id}
              to={`/calls/${call.id}`}
              className="flex items-center gap-4 px-5 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
            >
              <CallTypeBadge type={call.call_type} />
              <CallStateBadge state={call.call_state} />
              <span className="text-sm text-slate-500 ml-auto">
                {call.date ? format(new Date(call.date), 'dd MMM HH:mm') : '—'}
              </span>
              <span className="text-sm font-mono text-slate-400">
                {Math.round(call.seconds_talktime)}s
              </span>
            </Link>
          ))}
          {callsData?.items.length === 0 && (
            <p className="text-center text-slate-400 py-8 text-sm">No calls recorded</p>
          )}
        </div>
      </div>
    </div>
  )
}
