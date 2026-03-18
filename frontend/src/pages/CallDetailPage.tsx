import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, User, Brain, MessageSquare } from 'lucide-react'
import { format } from 'date-fns'
import { callsApi } from '../api/calls'
import { CallStateBadge } from '../components/calls/CallStateBadge'
import { CallTypeBadge } from '../components/calls/CallTypeBadge'
import { AudioPlayer } from '../components/calls/AudioPlayer'
import { PageSpinner } from '../components/ui/Spinner'

const AI_FIELDS: Array<{ key: string; label: string }> = [
  { key: 'conversation_topic', label: 'Topic' },
  { key: 'key_points_of_the_dialogue', label: 'Key Points' },
  { key: 'next_steps', label: 'Next Steps' },
  { key: 'operator_errors', label: 'Operator Errors' },
  { key: 'keywords', label: 'Keywords' },
  { key: 'clients_mood', label: "Client's Mood" },
  { key: 'operators_mood', label: "Operator's Mood" },
  { key: 'customer_satisfaction', label: 'Satisfaction' },
  { key: 'operator_professionalism', label: 'Professionalism' },
  { key: 'empathy', label: 'Empathy' },
  { key: 'clarity_of_communication', label: 'Clarity' },
  { key: 'attention_to_the_call', label: 'Attention' },
]

function formatDuration(s: number) {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return m ? `${m}m ${sec}s` : `${sec}s`
}

export default function CallDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data: call, isLoading } = useQuery({
    queryKey: ['call', id],
    queryFn: () => callsApi.getById(Number(id)),
    enabled: !!id,
  })

  if (isLoading) return <PageSpinner />
  if (!call) return <div className="text-slate-500 p-8">Call not found</div>

  const ai = call.ai_analytic

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Back */}
      <Link to="/calls" className="btn-ghost text-sm w-fit">
        <ArrowLeft size={14} /> Back to calls
      </Link>

      {/* Title */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">Call #{call.id}</h1>
        <CallTypeBadge type={call.call_type} />
        <CallStateBadge state={call.call_state} />
      </div>

      {/* Core details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card p-5 space-y-3">
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">Details</h2>
          <Row label="From" value={call.from_number} mono />
          <Row label="To" value={call.to_number} mono />
          <Row label="Date" value={call.date ? format(new Date(call.date), 'dd MMM yyyy HH:mm:ss') : '—'} />
          <Row label="Full duration" value={formatDuration(call.seconds_fulltime)} />
          <Row label="Talk time" value={formatDuration(call.seconds_talktime)} />
          <Row label="Callback" value={call.callback ? 'Yes' : 'No'} />
        </div>

        {call.user && (
          <div className="card p-5 space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-500 uppercase tracking-wide">
              <User size={14} /> Client
            </div>
            <Row label="Phone" value={call.user.phone_number} mono />
            <Row label="Name" value={call.user.name} />
            <Row label="Category" value={call.user.category?.name} />
            <Row label="Total calls" value={String(call.user.calls_count)} />
            <Link
              to={`/users/${call.user.id}`}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
            >
              View user profile →
            </Link>
          </div>
        )}
      </div>

      {/* Audio */}
      {call.mp3_link && (
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Recording
          </h2>
          <AudioPlayer src={call.mp3_link} />
        </div>
      )}

      {/* AI Analytics */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-4">
          <Brain size={16} className="text-purple-600" />
          <h2 className="text-sm font-semibold">AI Analytics</h2>
          {ai && (
            <span className={`badge ml-auto ${
              ai.processing_status === 'done'
                ? 'bg-green-100 text-green-700'
                : ai.processing_status === 'failed'
                ? 'bg-red-100 text-red-700'
                : 'bg-slate-100 text-slate-500'
            }`}>
              {ai.processing_status}
            </span>
          )}
        </div>

        {!ai || ai.processing_status === 'pending' ? (
          <p className="text-sm text-slate-400">Analysis not yet processed for this call.</p>
        ) : ai.processing_status === 'failed' ? (
          <p className="text-sm text-red-500">Processing failed. The call may lack a recording.</p>
        ) : (
          <div className="space-y-4">
            {ai.transcript && (
              <div>
                <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-500 uppercase">
                  <MessageSquare size={12} /> Transcript
                </div>
                <div className="bg-slate-50 dark:bg-slate-700 rounded-lg p-3 text-sm whitespace-pre-wrap max-h-48 overflow-y-auto">
                  {ai.transcript}
                </div>
              </div>
            )}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {AI_FIELDS.map(({ key, label }) => {
                const val = ai[key as keyof typeof ai]
                if (!val) return null
                return (
                  <div key={key} className="bg-slate-50 dark:bg-slate-700/50 rounded-lg p-3">
                    <p className="text-xs text-slate-500 mb-1">{label}</p>
                    <p className="text-sm font-medium">{String(val)}</p>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Row({ label, value, mono = false }: { label: string; value?: string | null; mono?: boolean }) {
  return (
    <div className="flex justify-between items-center gap-4">
      <span className="text-sm text-slate-500">{label}</span>
      <span className={`text-sm font-medium text-right ${mono ? 'font-mono' : ''}`}>
        {value ?? '—'}
      </span>
    </div>
  )
}
