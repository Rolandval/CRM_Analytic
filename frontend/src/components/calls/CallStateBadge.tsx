import type { CallState } from '../../api/types'

const STATE_STYLES: Record<CallState, string> = {
  ANSWER:   'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  NOANSWER: 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300',
  BUSY:     'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  FAILED:   'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
}

export function CallStateBadge({ state }: { state: CallState | null }) {
  if (!state) return <span className="badge bg-slate-100 text-slate-500">—</span>
  return <span className={`badge ${STATE_STYLES[state]}`}>{state}</span>
}
