import { PhoneIncoming, PhoneOutgoing } from 'lucide-react'
import type { CallType } from '../../api/types'

export function CallTypeBadge({ type }: { type: CallType | null }) {
  if (!type) return null
  if (type === 'IN') {
    return (
      <span className="badge bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-300 gap-1">
        <PhoneIncoming size={11} /> Inbound
      </span>
    )
  }
  return (
    <span className="badge bg-purple-50 text-purple-700 dark:bg-purple-900 dark:text-purple-300 gap-1">
      <PhoneOutgoing size={11} /> Outbound
    </span>
  )
}
