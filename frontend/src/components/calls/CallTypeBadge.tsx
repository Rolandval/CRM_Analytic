import { PhoneIncoming, PhoneOutgoing } from 'lucide-react'
import type { CallType } from '../../api/types'

export function CallTypeBadge({ type }: { type: CallType | null }) {
  if (!type) return null

  if (type === 'IN') {
    return (
      <span className="badge" style={{ background: 'rgba(99,102,241,0.10)', color: '#4338ca' }}>
        <PhoneIncoming size={11} strokeWidth={2.5} />
        Inbound
      </span>
    )
  }
  return (
    <span className="badge" style={{ background: 'rgba(139,92,246,0.10)', color: '#6d28d9' }}>
      <PhoneOutgoing size={11} strokeWidth={2.5} />
      Outbound
    </span>
  )
}
