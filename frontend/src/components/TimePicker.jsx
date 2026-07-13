import { useEffect, useRef, useState } from 'react'
import { Clock, ChevronUp, ChevronDown } from 'pixelarticons/react'

const pad = (n) => String(n).padStart(2, '0')
const wrap = (n, max) => ((n % max) + max) % max

function Stepper({ value, onStep, label }) {
  return (
    <div className="flex flex-col items-center gap-0.5 sm:gap-1">
      <button
        type="button"
        onClick={() => onStep(1)}
        className="p-1 text-gray-400 hover:text-cyber-secondary"
        aria-label={`Увеличить ${label}`}
      >
        <ChevronUp width={14} height={14} />
      </button>
      <span className="w-7 text-center font-mono text-base text-gray-100 sm:w-9 sm:text-lg">{pad(value)}</span>
      <button
        type="button"
        onClick={() => onStep(-1)}
        className="p-1 text-gray-400 hover:text-cyber-secondary"
        aria-label={`Уменьшить ${label}`}
      >
        <ChevronDown width={14} height={14} />
      </button>
    </div>
  )
}

export default function TimePicker({ value, onChange, disabled = false, className = '' }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  const [hour, minute] = value ? value.split(':').map(Number) : [0, 0]

  useEffect(() => {
    if (!open) return
    const handleClick = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false)
    }
    const handleKey = (e) => {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    document.addEventListener('keydown', handleKey)
    return () => {
      document.removeEventListener('mousedown', handleClick)
      document.removeEventListener('keydown', handleKey)
    }
  }, [open])

  const commit = (nextHour, nextMinute) => {
    onChange(`${pad(nextHour)}:${pad(nextMinute)}`)
  }

  const stepHour = (delta) => commit(wrap(hour + delta, 24), minute)
  const stepMinute = (delta) => commit(hour, wrap(minute + delta, 60))

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setOpen((o) => !o)}
        className={`flex w-full items-center gap-2 bg-cyber-muted px-3 py-2 text-left text-sm disabled:opacity-40 ${
          value ? 'text-gray-100' : 'text-gray-500'
        }`}
      >
        <Clock width={16} height={16} className="shrink-0 text-gray-400" />
        {value || '--:--'}
      </button>

      {open && !disabled && (
        <div className="absolute z-40 mt-1 border-2 border-cyber-secondary bg-cyber-card p-2 pixel-shadow-secondary sm:p-3">
          <div className="flex items-center gap-1 sm:gap-2">
            <Stepper value={hour} onStep={stepHour} label="часы" />
            <span className="pb-4 text-base text-gray-500 sm:pb-6 sm:text-lg">:</span>
            <Stepper value={minute} onStep={stepMinute} label="минуты" />
          </div>

          <div className="mt-1 flex gap-1 sm:mt-2 sm:gap-2">
            {value && (
              <button
                type="button"
                onClick={() => {
                  onChange('')
                  setOpen(false)
                }}
                className="flex-1 py-1 text-center text-xs text-gray-500 hover:text-cyber-danger"
              >
                Очистить
              </button>
            )}
            <button
              type="button"
              onClick={() => {
                if (!value) commit(hour, minute)
                setOpen(false)
              }}
              className="flex-1 py-1 text-center text-xs text-cyber-secondary hover:text-glow"
            >
              Готово
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
