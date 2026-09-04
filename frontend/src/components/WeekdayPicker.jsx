import TimePicker from './TimePicker'

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

// value: массив чисел 0..6 (Пн=0 ... Вс=6), совпадает с backend scheduled_days.
// times/onTimesChange — необязательны: если переданы, под каждым выбранным
// днём появляется TimePicker со своим временем напоминания (reminder_times).
// Само распикивание дня чистит его время из times — родителю не нужно
// самому следить за согласованностью двух состояний.
export default function WeekdayPicker({ value, onChange, times, onTimesChange, className = '' }) {
  const toggle = (day) => {
    if (value.includes(day)) {
      onChange(value.filter((d) => d !== day))
      if (onTimesChange && times && day in times) {
        const next = { ...times }
        delete next[day]
        onTimesChange(next)
      }
    } else {
      onChange([...value, day].sort((a, b) => a - b))
    }
  }

  const setTime = (day, time) => {
    if (!onTimesChange) return
    const next = { ...times }
    if (time) {
      next[day] = time
    } else {
      delete next[day]
    }
    onTimesChange(next)
  }

  return (
    <div className={`flex flex-wrap gap-3 ${className}`}>
      {WEEKDAYS.map((label, day) => {
        const active = value.includes(day)
        return (
          <div key={day} className="flex flex-col items-center gap-1">
            <button
              type="button"
              onClick={() => toggle(day)}
              aria-pressed={active}
              className={`h-8 w-10 shrink-0 rounded-none text-xs font-mono uppercase transition-all ${
                active
                  ? 'bg-cyber-secondary text-cyber-bg pixel-shadow-secondary'
                  : 'border-2 border-cyber-border bg-cyber-muted text-gray-400 hover:text-gray-200'
              }`}
            >
              {label}
            </button>
            {active && onTimesChange && (
              <TimePicker value={times?.[day] ?? ''} onChange={(time) => setTime(day, time)} className="w-20" />
            )}
          </div>
        )
      })}
    </div>
  )
}
