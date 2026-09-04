import { useState } from 'react'
import { useCreateQuest } from '../hooks/useQuests'
import { useStats } from '../hooks/useStats'
import { fromDateAndTimeInputValue } from '../utils/datetime'
import Button from './Button'
import Select from './Select'
import DatePicker from './DatePicker'
import TimePicker from './TimePicker'
import WeekdayPicker from './WeekdayPicker'

const questTypes = [
  { value: 'once', label: 'Разовый' },
  { value: 'daily', label: 'Ежедневный' },
  { value: 'weekly', label: 'Еженедельный' },
  { value: 'habit', label: 'Привычка' },
]

export default function QuestForm() {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [questType, setQuestType] = useState('once')
  const [statId, setStatId] = useState('')
  const [statId2, setStatId2] = useState('')
  const [scheduledDays, setScheduledDays] = useState([])
  const [reminderTime, setReminderTime] = useState('')
  const [dateEnd, setDateEnd] = useState('')
  const [timeEnd, setTimeEnd] = useState('')

  const { data: stats } = useStats()
  const { mutate, isPending, error } = useCreateQuest()

  const statOptions = [
    { value: '', label: 'Без привязки к стату' },
    ...(stats ?? []).map((s) => ({ value: String(s.id), label: s.name })),
  ]
  // второй стат не может дублировать первый
  const statOptions2 = statOptions.filter((o) => o.value === '' || o.value !== statId)

  const isHabit = questType === 'habit'

  const handleQuestTypeChange = (value) => {
    setQuestType(value)
    if (value !== 'habit') {
      setScheduledDays([])
      setReminderTime('')
    }
  }

  // Опция пропадает из второго списка, но сама по себе не сбрасывается —
  // без этого форма молча ушла бы на сервер с дублем статов и словила 422.
  const handleStatIdChange = (value) => {
    setStatId(value)
    if (value && value === statId2) setStatId2('')
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    // На создании время одно на все выбранные дни — своё время под каждый
    // день можно будет выставить потом через "Изменить" (QuestCard).
    const reminderTimes =
      isHabit && reminderTime && scheduledDays.length > 0
        ? Object.fromEntries(scheduledDays.map((day) => [day, reminderTime]))
        : null
    mutate(
      {
        name,
        description: description || null,
        quest_type: questType,
        stat_id: statId ? Number(statId) : null,
        stat_id_2: statId2 ? Number(statId2) : null,
        date_end: fromDateAndTimeInputValue(dateEnd, timeEnd),
        scheduled_days: isHabit && scheduledDays.length > 0 ? scheduledDays : null,
        reminder_times: reminderTimes,
      },
      {
        onSuccess: () => {
          setName('')
          setDescription('')
          setQuestType('once')
          setStatId('')
          setStatId2('')
          setScheduledDays([])
          setReminderTime('')
          setDateEnd('')
          setTimeEnd('')
        },
      }
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3 rounded-none border-2 border-cyber-border bg-cyber-card p-4"
    >
      <h2 className="font-display text-sm text-gray-300">НОВЫЙ КВЕСТ</h2>

      <div className="cyber-input-wrapper">
        <input
          type="text"
          placeholder="Название"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="cyber-input w-full rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
          required
        />
      </div>
      <div className="cyber-input-wrapper">
        <textarea
          placeholder="Описание (необязательно)"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="cyber-input w-full rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
          rows={2}
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Select value={questType} onChange={handleQuestTypeChange} options={questTypes} className="w-44" />
        <Select value={statId} onChange={handleStatIdChange} options={statOptions} className="w-52" />
        <Select value={statId2} onChange={setStatId2} options={statOptions2} className="w-52" />

        <DatePicker value={dateEnd} onChange={setDateEnd} className="w-40" />
        <TimePicker value={timeEnd} onChange={setTimeEnd} disabled={!dateEnd} className="w-28" />

        <Button type="submit" variant="primary" disabled={isPending} className="ml-auto">
          {isPending ? 'Создаём...' : 'Создать квест'}
        </Button>
      </div>

      {isHabit && (
        <div>
          <p className="mb-1 text-xs uppercase tracking-wide text-gray-500">
            Дни недели (пусто — без расписания, как раньше)
          </p>
          <p className="mb-1 text-xs text-gray-500">
            Пропуск дня бьёт по боссу. Выполнение вне расписания засчитается в серию, но стоит 5 HP.
          </p>
          <WeekdayPicker value={scheduledDays} onChange={setScheduledDays} />

          <div className="mt-2 flex items-center gap-2">
            <TimePicker
              value={reminderTime}
              onChange={setReminderTime}
              disabled={scheduledDays.length === 0}
              className="w-28"
            />
            <p className="text-xs text-gray-500">
              Время напоминания — необязательно, одно на все выбранные дни. Своё время на каждый день
              можно будет настроить в редактировании.
            </p>
          </div>
        </div>
      )}

      {error && <p className="text-sm text-cyber-danger">Не удалось создать квест</p>}
    </form>
  )
}
