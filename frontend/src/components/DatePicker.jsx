import { useEffect, useRef, useState } from 'react'
import { Calendar, ChevronLeft, ChevronRight } from 'pixelarticons/react'

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const MONTHS = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь',
]

const pad = (n) => String(n).padStart(2, '0')
const toValue = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
const isSameDay = (a, b) =>
  !!a && !!b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()

// Builds a 6-week grid starting on Monday, using real Date arithmetic so
// month/year rollover (e.g. "day -2" of March) is handled by JS itself.
function buildGrid(year, month) {
  const firstWeekday = (new Date(year, month, 1).getDay() + 6) % 7
  const gridStart = new Date(year, month, 1 - firstWeekday)
  return Array.from({ length: 42 }, (_, i) => {
    const date = new Date(gridStart)
    date.setDate(gridStart.getDate() + i)
    return date
  })
}

export default function DatePicker({ value, onChange, className = '', placeholder = 'ДД.ММ.ГГГГ' }) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  const selectedDate = value ? new Date(`${value}T00:00:00`) : null
  const today = new Date()
  const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())

  const [viewYear, setViewYear] = useState((selectedDate ?? today).getFullYear())
  const [viewMonth, setViewMonth] = useState((selectedDate ?? today).getMonth())

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

  const openCalendar = () => {
    const base = selectedDate ?? today
    setViewYear(base.getFullYear())
    setViewMonth(base.getMonth())
    setOpen(true)
  }

  const shiftMonth = (delta) => {
    const d = new Date(viewYear, viewMonth + delta, 1)
    setViewYear(d.getFullYear())
    setViewMonth(d.getMonth())
  }

  const handleSelect = (date) => {
    onChange(toValue(date))
    setOpen(false)
  }

  const canGoPrevMonth = viewYear > today.getFullYear() || (viewYear === today.getFullYear() && viewMonth > today.getMonth())

  const displayLabel = selectedDate
    ? `${pad(selectedDate.getDate())}.${pad(selectedDate.getMonth() + 1)}.${selectedDate.getFullYear()}`
    : placeholder

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <button
        type="button"
        onClick={() => (open ? setOpen(false) : openCalendar())}
        className={`flex w-full items-center gap-2 bg-cyber-muted px-3 py-2 text-left text-sm ${
          value ? 'text-gray-100' : 'text-gray-500'
        }`}
      >
        <Calendar width={16} height={16} className="shrink-0 text-gray-400" />
        {displayLabel}
      </button>

      {open && (
        <div className="absolute z-40 mt-1 w-56 border-2 border-cyber-secondary bg-cyber-card p-2 pixel-shadow-secondary sm:w-64 sm:p-3">
          <div className="mb-1 flex items-center justify-between sm:mb-2">
            <button
              type="button"
              onClick={() => shiftMonth(-1)}
              disabled={!canGoPrevMonth}
              className="p-1 text-gray-400 hover:text-cyber-secondary disabled:opacity-30 disabled:hover:text-gray-400"
              aria-label="Предыдущий месяц"
            >
              <ChevronLeft width={14} height={14} />
            </button>
            <span className="text-xs text-gray-100 sm:text-sm">
              {MONTHS[viewMonth]} {viewYear}
            </span>
            <button
              type="button"
              onClick={() => shiftMonth(1)}
              className="p-1 text-gray-400 hover:text-cyber-secondary"
              aria-label="Следующий месяц"
            >
              <ChevronRight width={14} height={14} />
            </button>
          </div>

          <div className="grid grid-cols-7 gap-0.5 text-center text-[10px] text-gray-500 sm:gap-1 sm:text-xs">
            {WEEKDAYS.map((w) => (
              <span key={w}>{w}</span>
            ))}
          </div>
          <div className="mt-1 grid grid-cols-7 gap-0.5 sm:gap-1">
            {buildGrid(viewYear, viewMonth).map((date) => {
              const inMonth = date.getMonth() === viewMonth
              const selected = isSameDay(date, selectedDate)
              const isToday = isSameDay(date, today)
              const isPast = date < todayStart
              return (
                <button
                  key={date.toISOString()}
                  type="button"
                  onClick={() => handleSelect(date)}
                  disabled={isPast}
                  className={`flex h-7 items-center justify-center text-xs transition-colors disabled:cursor-not-allowed disabled:text-gray-700 disabled:hover:bg-transparent sm:h-8 sm:text-sm ${
                    selected
                      ? 'bg-cyber-secondary text-cyber-bg'
                      : isToday
                        ? 'border-2 border-cyber-secondary text-cyber-secondary'
                        : inMonth
                          ? 'text-gray-200 hover:bg-cyber-muted'
                          : 'text-gray-600 hover:bg-cyber-muted'
                  }`}
                >
                  {date.getDate()}
                </button>
              )
            })}
          </div>

          {value && (
            <button
              type="button"
              onClick={() => {
                onChange('')
                setOpen(false)
              }}
              className="mt-1 w-full py-1 text-center text-xs text-gray-500 hover:text-cyber-danger sm:mt-2"
            >
              Очистить
            </button>
          )}
        </div>
      )}
    </div>
  )
}
