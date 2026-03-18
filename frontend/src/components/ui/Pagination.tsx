import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Props {
  page: number
  pages: number
  total: number
  onPage: (p: number) => void
}

export function Pagination({ page, pages, total, onPage }: Props) {
  if (pages <= 1) return null

  return (
    <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400 mt-4">
      <span>{total} total</span>
      <div className="flex items-center gap-1">
        <button
          className="btn-ghost px-2 py-1"
          onClick={() => onPage(page - 1)}
          disabled={page <= 1}
        >
          <ChevronLeft size={16} />
        </button>
        <span className="px-3 py-1 text-slate-700 dark:text-slate-200 font-medium">
          {page} / {pages}
        </span>
        <button
          className="btn-ghost px-2 py-1"
          onClick={() => onPage(page + 1)}
          disabled={page >= pages}
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  )
}
