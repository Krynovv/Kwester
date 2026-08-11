const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

// value: массив чисел 0..6 (Пн=0 ... Вс=6), совпадает с backend scheduled_days.
export default function WeekdayPicker({ value, onChange, className = '' }) {
  const toggle = (day) => {
    if (value.includes(day)) {
      onChange(value.filter((d) => d !== day))
    } else {
      onChange([...value, day].sort((a, b) => a - b))
    }
  }

  return (
    <div className={`flex flex-wrap gap-1.5 ${className}`}>
      {WEEKDAYS.map((label, day) => {
        const active = value.includes(day)
        return (
          <button
            key={day}
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
        )
      })}
    </div>
  )
}
