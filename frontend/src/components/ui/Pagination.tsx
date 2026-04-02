import { ChevronLeft, ChevronRight } from 'lucide-react'

interface Props {
  page: number
  pages: number
  total: number
  onPage: (p: number) => void
}

export function Pagination({ page, pages, total, onPage }: Props) {
  if (pages <= 1) return null

  const getPages = (): (number | '...')[] => {
    const delta = 2
    const range: (number | '...')[] = [1]
    const left = Math.max(2, page - delta)
    const right = Math.min(pages - 1, page + delta)

    if (left > 2) range.push('...')
    for (let i = left; i <= right; i++) range.push(i)
    if (right < pages - 1) range.push('...')
    if (pages > 1) range.push(pages)
    return range
  }

  return (
    <div className="flex items-center justify-between mt-5 animate-fade-in">
      <span className="text-sm text-slate-400 font-medium">
        {total.toLocaleString()} records
      </span>

      <div className="flex items-center gap-1.5">
        <button
          onClick={() => onPage(page - 1)}
          disabled={page <= 1}
          className="w-9 h-9 flex items-center justify-center rounded-xl text-slate-500
                     bg-white border border-black/[0.07] shadow-card
                     hover:bg-slate-50 hover:shadow-card-hover
                     disabled:opacity-30 disabled:cursor-not-allowed
                     transition-all duration-150"
        >
          <ChevronLeft size={15} />
        </button>

        {getPages().map((p, i) =>
          p === '...' ? (
            <span key={`d${i}`} className="w-9 h-9 flex items-center justify-center text-slate-400 text-sm">
              ·····
            </span>
          ) : (
            <button
              key={p}
              onClick={() => onPage(p as number)}
              className={`w-9 h-9 flex items-center justify-center rounded-xl text-sm font-semibold
                          transition-all duration-150 ${
                p === page
                  ? 'text-white shadow-btn-glow-sm scale-105'
                  : 'text-slate-600 bg-white border border-black/[0.07] shadow-card hover:bg-slate-50 hover:shadow-card-hover'
              }`}
              style={p === page ? { background: 'linear-gradient(135deg, #6366f1, #3b82f6)' } : {}}
            >
              {p}
            </button>
          )
        )}

        <button
          onClick={() => onPage(page + 1)}
          disabled={page >= pages}
          className="w-9 h-9 flex items-center justify-center rounded-xl text-slate-500
                     bg-white border border-black/[0.07] shadow-card
                     hover:bg-slate-50 hover:shadow-card-hover
                     disabled:opacity-30 disabled:cursor-not-allowed
                     transition-all duration-150"
        >
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  )
}
