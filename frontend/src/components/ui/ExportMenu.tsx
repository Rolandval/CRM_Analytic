import { useEffect, useRef, useState } from 'react'
import { Download, FileSpreadsheet, FileText, FileType, Loader2, Check } from 'lucide-react'

interface ExportOption {
  format: 'csv' | 'xlsx' | 'txt'
  label: string
  description: string
  icon: typeof Download
  accent: string
}

const OPTIONS: ExportOption[] = [
  {
    format: 'xlsx',
    label: 'Excel',
    description: 'XLSX з форматуванням',
    icon: FileSpreadsheet,
    accent: 'text-emerald-600 bg-emerald-50',
  },
  {
    format: 'csv',
    label: 'CSV',
    description: 'Universal comma-separated',
    icon: FileType,
    accent: 'text-blue-600 bg-blue-50',
  },
  {
    format: 'txt',
    label: 'Text',
    description: 'Pipe-delimited table',
    icon: FileText,
    accent: 'text-amber-600 bg-amber-50',
  },
]

interface Props {
  onExport: (format: 'csv' | 'xlsx' | 'txt') => Promise<void>
  disabled?: boolean
  recordCount?: number
}

export function ExportMenu({ onExport, disabled, recordCount }: Props) {
  const [open, setOpen] = useState(false)
  const [loadingFormat, setLoadingFormat] = useState<string | null>(null)
  const [successFormat, setSuccessFormat] = useState<string | null>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [open])

  const handleClick = async (format: 'csv' | 'xlsx' | 'txt') => {
    if (loadingFormat) return
    setLoadingFormat(format)
    try {
      await onExport(format)
      setSuccessFormat(format)
      setTimeout(() => {
        setSuccessFormat(null)
        setOpen(false)
      }, 1200)
    } finally {
      setLoadingFormat(null)
    }
  }

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => setOpen(v => !v)}
        disabled={disabled}
        className="btn-secondary h-10 gap-2"
      >
        <Download size={14} />
        Export
        {recordCount !== undefined && recordCount > 0 && (
          <span className="text-xs text-slate-400 font-normal">
            ({recordCount.toLocaleString()})
          </span>
        )}
      </button>

      {open && (
        <div
          className="absolute right-0 top-full mt-2 w-72 bg-white rounded-2xl shadow-popover border border-black/[0.06] overflow-hidden z-40 animate-scale-in"
          style={{ transformOrigin: 'top right' }}
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-black/[0.05] bg-slate-50/50">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Download as
            </p>
            {recordCount !== undefined && (
              <p className="text-xs text-slate-400 mt-0.5">
                {recordCount.toLocaleString()} record{recordCount === 1 ? '' : 's'} with current filters
              </p>
            )}
          </div>

          {/* Options */}
          <div className="p-1.5">
            {OPTIONS.map(opt => {
              const Icon = opt.icon
              const isLoading = loadingFormat === opt.format
              const isSuccess = successFormat === opt.format
              return (
                <button
                  key={opt.format}
                  onClick={() => handleClick(opt.format)}
                  disabled={loadingFormat !== null}
                  className="w-full flex items-center gap-3 p-2.5 rounded-xl hover:bg-slate-50 transition-colors text-left disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${opt.accent}`}>
                    {isLoading ? (
                      <Loader2 size={15} className="animate-spin" />
                    ) : isSuccess ? (
                      <Check size={15} strokeWidth={2.5} />
                    ) : (
                      <Icon size={15} strokeWidth={2} />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-slate-800">{opt.label}</p>
                    <p className="text-xs text-slate-400">
                      {isLoading ? 'Preparing…' : isSuccess ? 'Downloaded!' : opt.description}
                    </p>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

/** Helper to trigger browser download from a Blob */
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
