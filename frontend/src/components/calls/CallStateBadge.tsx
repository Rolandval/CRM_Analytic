import type { CallState } from '../../api/types'

const CFG: Record<CallState, { label: string; dot: string; bg: string; text: string }> = {
  ANSWER:   { label: 'Answered',  dot: '#10b981', bg: 'rgba(16,185,129,0.10)', text: '#065f46' },
  NOANSWER: { label: 'No Answer', dot: '#94a3b8', bg: 'rgba(148,163,184,0.12)', text: '#475569' },
  BUSY:     { label: 'Busy',      dot: '#f59e0b', bg: 'rgba(245,158,11,0.12)',  text: '#92400e' },
  FAILED:   { label: 'Failed',    dot: '#f43f5e', bg: 'rgba(244,63,94,0.10)',   text: '#9f1239' },
}

export function CallStateBadge({ state }: { state: CallState | null }) {
  if (!state) {
    return (
      <span className="badge" style={{ background: 'rgba(0,0,0,0.05)', color: '#94a3b8' }}>—</span>
    )
  }
  const c = CFG[state]
  return (
    <span className="badge" style={{ background: c.bg, color: c.text }}>
      <span className="badge-dot" style={{ background: c.dot }} />
      {c.label}
    </span>
  )
}
