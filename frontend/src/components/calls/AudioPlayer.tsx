import { useRef, useState } from 'react'
import { Play, Pause, Volume2 } from 'lucide-react'

interface Props { src: string }

export function AudioPlayer({ src }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)

  const toggle = () => {
    if (!audioRef.current) return
    if (playing) audioRef.current.pause()
    else audioRef.current.play()
    setPlaying(!playing)
  }

  const fmt = (s: number) => {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex items-center gap-3 bg-slate-100 dark:bg-slate-700 rounded-lg px-3 py-2">
      <audio
        ref={audioRef}
        src={src}
        onTimeUpdate={() => {
          const a = audioRef.current
          if (a) setProgress((a.currentTime / a.duration) * 100)
        }}
        onLoadedMetadata={() => setDuration(audioRef.current?.duration ?? 0)}
        onEnded={() => setPlaying(false)}
      />
      <button onClick={toggle} className="text-blue-600 dark:text-blue-400 hover:opacity-80">
        {playing ? <Pause size={18} /> : <Play size={18} />}
      </button>
      <div className="flex-1 h-1.5 bg-slate-300 dark:bg-slate-600 rounded-full relative">
        <div
          className="h-full bg-blue-600 rounded-full transition-all"
          style={{ width: `${progress}%` }}
        />
        <input
          type="range"
          min={0} max={100}
          value={progress}
          onChange={(e) => {
            const a = audioRef.current
            if (a) { a.currentTime = (Number(e.target.value) / 100) * a.duration }
          }}
          className="absolute inset-0 opacity-0 cursor-pointer w-full"
        />
      </div>
      <span className="text-xs text-slate-500 tabular-nums">
        {duration > 0 ? fmt(duration) : '--:--'}
      </span>
      <Volume2 size={14} className="text-slate-400" />
    </div>
  )
}
