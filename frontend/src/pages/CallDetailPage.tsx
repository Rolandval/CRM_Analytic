import { useQuery } from '@tanstack/react-query'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, User, Brain, MessageSquare, Phone, Clock } from 'lucide-react'
import { format } from 'date-fns'
import { callsApi } from '../api/calls'
import { CallStateBadge } from '../components/calls/CallStateBadge'
import { CallTypeBadge } from '../components/calls/CallTypeBadge'
import { AudioPlayer } from '../components/calls/AudioPlayer'
import { PageSpinner } from '../components/ui/Spinner'

const AI_FIELDS: Array<{ key: string; label: string }> = [
  { key: 'conversation_topic',        label: 'Topic' },
  { key: 'key_points_of_the_dialogue', label: 'Key Points' },
  { key: 'next_steps',                label: 'Next Steps' },
  { key: 'operator_errors',           label: 'Operator Errors' },
  { key: 'keywords',                  label: 'Keywords' },
  { key: 'clients_mood',              label: "Client's Mood" },
  { key: 'operators_mood',            label: "Operator's Mood" },
  { key: 'customer_satisfaction',     label: 'Satisfaction' },
  { key: 'operator_professionalism',  label: 'Professionalism' },
  { key: 'empathy',                   label: 'Empathy' },
  { key: 'clarity_of_communication',  label: 'Clarity' },
  { key: 'attention_to_the_call',     label: 'Attention' },
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
    <div className="space-y-5 max-w-4xl animate-slide-up">

      {/* Back */}
      <Link to="/calls"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors font-medium">
        <ArrowLeft size={14} />
        Back to calls
      </Link>

      {/* Title */}
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl font-bold tracking-tight text-gradient">Call #{call.id}</h1>
        <CallTypeBadge type={call.call_type} />
        <CallStateBadge state={call.call_state} />
      </div>

      {/* Details grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card overflow-hidden">
          <div className="h-1" style={{ background: 'linear-gradient(90deg, #6366f1, #3b82f6)' }} />
          <div className="p-5">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                   style={{ background: 'rgba(99,102,241,0.10)' }}>
                <Phone size={14} className="text-brand-600" strokeWidth={2.5} />
              </div>
              <h2 className="font-bold text-slate-900 text-sm">Call Details</h2>
            </div>
            <div className="space-y-1">
              <Row label="From" value={call.from_number} mono />
              <Row label="To"   value={call.to_number} mono />
              <Row label="Date" value={call.date ? format(new Date(call.date), 'dd MMM yyyy, HH:mm:ss') : '—'} />
              <Row label="Full duration" value={formatDuration(call.seconds_fulltime)} />
              <Row label="Talk time" value={formatDuration(call.seconds_talktime)} />
              <Row label="Callback" value={call.callback ? 'Yes' : 'No'} />
            </div>
          </div>
        </div>

        {call.user && (
          <div className="card overflow-hidden">
            <div className="h-1" style={{ background: 'linear-gradient(90deg, #8b5cf6, #6366f1)' }} />
            <div className="p-5">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                     style={{ background: 'rgba(139,92,246,0.10)' }}>
                  <User size={14} className="text-violet-600" strokeWidth={2.5} />
                </div>
                <h2 className="font-bold text-slate-900 text-sm">Client</h2>
              </div>
              <div className="space-y-1">
                <Row label="Phone"       value={call.user.phone_number} mono />
                <Row label="Name"        value={call.user.name} />
                <Row label="Category"    value={call.user.category?.name} />
                <Row label="Total calls" value={String(call.user.calls_count)} />
              </div>
              <Link to={`/users/${call.user.id}`}
                className="mt-4 inline-flex items-center gap-1 text-sm text-brand-600 font-semibold hover:underline">
                View client profile →
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Audio */}
      {call.mp3_link && (
        <div className="card overflow-hidden">
          <div className="h-1" style={{ background: 'linear-gradient(90deg, #10b981, #059669)' }} />
          <div className="p-5">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                   style={{ background: 'rgba(16,185,129,0.10)' }}>
                <Clock size={14} className="text-emerald-600" strokeWidth={2.5} />
              </div>
              <h2 className="font-bold text-slate-900 text-sm">Recording</h2>
            </div>
            <AudioPlayer src={call.mp3_link} />
          </div>
        </div>
      )}

      {/* AI Analytics */}
      <div className="card overflow-hidden">
        <div className="h-1" style={{ background: 'linear-gradient(90deg, #8b5cf6, #a855f7, #6366f1)' }} />
        <div className="p-5">
          <div className="flex items-center gap-2.5 mb-5">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center"
                 style={{ background: 'rgba(139,92,246,0.10)' }}>
              <Brain size={14} className="text-violet-600" strokeWidth={2.5} />
            </div>
            <h2 className="font-bold text-slate-900 text-sm">AI Analytics</h2>
            {ai && (
              <span className="badge text-xs font-semibold ml-auto"
                    style={
                      ai.processing_status === 'done'
                        ? { background: 'rgba(16,185,129,0.10)', color: '#065f46' }
                        : ai.processing_status === 'failed'
                        ? { background: 'rgba(244,63,94,0.10)', color: '#9f1239' }
                        : { background: 'rgba(0,0,0,0.06)', color: '#64748b' }
                    }>
                <span className="badge-dot" style={{
                  background: ai.processing_status === 'done' ? '#10b981'
                    : ai.processing_status === 'failed' ? '#f43f5e' : '#94a3b8'
                }} />
                {ai.processing_status}
              </span>
            )}
          </div>

          {!ai || ai.processing_status === 'pending' ? (
            <div className="flex items-center gap-2 text-sm text-slate-400 py-2">
              <Brain size={15} strokeWidth={1.5} />
              Analysis not yet processed for this call.
            </div>
          ) : ai.processing_status === 'failed' ? (
            <p className="text-sm text-rose-500 py-2">Processing failed. The call may lack a recording.</p>
          ) : (
            <div className="space-y-4">
              {ai.transcript && (
                <div>
                  <div className="flex items-center gap-2 mb-2.5 section-title">
                    <MessageSquare size={12} /> Transcript
                  </div>
                  <div className="rounded-xl p-4 text-sm whitespace-pre-wrap max-h-52 overflow-y-auto
                                  text-slate-700 leading-relaxed"
                       style={{ background: '#F8F9FC', border: '1px solid rgba(0,0,0,0.06)' }}>
                    {ai.transcript}
                  </div>
                </div>
              )}
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {AI_FIELDS.map(({ key, label }) => {
                  const val = ai[key as keyof typeof ai]
                  if (!val) return null
                  return (
                    <div key={key}
                      className="rounded-xl p-3.5 transition-shadow hover:shadow-card"
                      style={{ background: '#F8F9FC', border: '1px solid rgba(0,0,0,0.05)' }}>
                      <p className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider mb-1">{label}</p>
                      <p className="text-sm font-bold text-slate-800">{String(val)}</p>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Row({ label, value, mono = false }: { label: string; value?: string | null; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-4 py-2 border-b border-black/[0.04] last:border-0">
      <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider flex-shrink-0">{label}</span>
      <span className={`text-sm font-semibold text-right text-slate-800 ${mono ? 'font-mono' : ''}`}>
        {value ?? <span className="text-slate-300 font-normal">—</span>}
      </span>
    </div>
  )
}
