import { useState } from 'react'
import { Coins, Fire } from 'pixelarticons/react'
import { useCompleteQuest, useDeleteQuest, useUpdateQuest } from '../hooks/useQuests'
import { useStats } from '../hooks/useStats'
import { toDateInputValue, toTimeInputValue, fromDateAndTimeInputValue } from '../utils/datetime'
import Button from './Button'
import Select from './Select'
import DatePicker from './DatePicker'
import TimePicker from './TimePicker'
import WeekdayPicker from './WeekdayPicker'

const typeLabels = {
  once: 'Разовый',
  daily: 'Ежедневный',
  weekly: 'Еженедельный',
  habit: 'Привычка',
}

const WEEKDAY_LABELS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

const statusBorder = {
  active: 'border-cyber-border',
  done: 'border-cyber-accent/50 opacity-60',
  failed: 'border-cyber-primary/50 opacity-60',
}

function isCompletedToday(quest) {
  if (!quest.last_completed_at) return false
  const last = new Date(quest.last_completed_at)
  const now = new Date()
  return (
    last.getFullYear() === now.getFullYear() &&
    last.getMonth() === now.getMonth() &&
    last.getDate() === now.getDate()
  )
}

export default function QuestCard({ quest, statName, statName2 }) {
  const [isEditing, setIsEditing] = useState(false)
  const [name, setName] = useState(quest.name)
  const [description, setDescription] = useState(quest.description ?? '')
  const [statId, setStatId] = useState(quest.stat_id ? String(quest.stat_id) : '')
  const [statId2, setStatId2] = useState(quest.stat_id_2 ? String(quest.stat_id_2) : '')
  const [scheduledDays, setScheduledDays] = useState(quest.scheduled_days ?? [])
  const [dateEnd, setDateEnd] = useState(toDateInputValue(quest.date_end))
  const [timeEnd, setTimeEnd] = useState(toTimeInputValue(quest.date_end))

  const { data: stats } = useStats()
  const { mutate: complete, isPending: completing } = useCompleteQuest()
  const { mutate: remove, isPending: deleting } = useDeleteQuest()
  const { mutate: update, isPending: updating, error: updateError } = useUpdateQuest()

  const statOptions = [
    { value: '', label: 'Без привязки к стату' },
    ...(stats ?? []).map((s) => ({ value: String(s.id), label: s.name })),
  ]
  const statOptions2 = statOptions.filter((o) => o.value === '' || o.value !== statId)

  const isScheduledHabit = quest.quest_type === 'habit' && (quest.scheduled_days?.length ?? 0) > 0
  const doneToday = isScheduledHabit && isCompletedToday(quest)
  const canComplete = quest.status === 'active' && !doneToday

  // См. QuestForm: опция исчезает из второго списка, но значение остаётся в стейте.
  const handleStatIdChange = (value) => {
    setStatId(value)
    if (value && value === statId2) setStatId2('')
  }

  const handleSave = (e) => {
    e.preventDefault()
    update(
      {
        id: quest.id,
        data: {
          name,
          description: description || null,
          stat_id: statId ? Number(statId) : null,
          stat_id_2: statId2 ? Number(statId2) : null,
          date_end: fromDateAndTimeInputValue(dateEnd, timeEnd),
          ...(quest.quest_type === 'habit'
            ? { scheduled_days: scheduledDays.length > 0 ? scheduledDays : null }
            : {}),
        },
      },
      { onSuccess: () => setIsEditing(false) }
    )
  }

  if (isEditing) {
    return (
      <form
        onSubmit={handleSave}
        className="space-y-2 rounded-none border-2 border-cyber-secondary bg-cyber-card p-4"
      >
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-none bg-cyber-muted px-3 py-2 font-sans text-sm text-gray-100"
          required
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full rounded-none bg-cyber-muted px-3 py-2 font-sans text-sm text-gray-100"
        />
        <div className="flex flex-wrap gap-3">
          <Select value={statId} onChange={handleStatIdChange} options={statOptions} className="w-52" />
          <Select value={statId2} onChange={setStatId2} options={statOptions2} className="w-52" />
          <DatePicker value={dateEnd} onChange={setDateEnd} className="w-40" />
          <TimePicker value={timeEnd} onChange={setTimeEnd} disabled={!dateEnd} className="w-28" />
        </div>

        {quest.quest_type === 'habit' && (
          <div>
            <p className="mb-1 text-xs uppercase tracking-wide text-gray-500">
              Дни недели (пусто — без расписания)
            </p>
            <p className="mb-1 text-xs text-gray-500">
              Пропуск дня бьёт по боссу. Выполнение вне расписания засчитается в серию, но стоит 5 HP.
            </p>
            <WeekdayPicker value={scheduledDays} onChange={setScheduledDays} />
          </div>
        )}

        {updateError && <p className="text-sm text-cyber-danger">Не удалось сохранить</p>}

        <div className="flex gap-2">
          <Button type="submit" variant="secondary" disabled={updating}>
            {updating ? 'Сохраняем...' : 'Сохранить'}
          </Button>
          <Button type="button" variant="ghost" onClick={() => setIsEditing(false)}>
            Отмена
          </Button>
        </div>
      </form>
    )
  }

  return (
    <div className={`rounded-none border-2 ${statusBorder[quest.status]} bg-cyber-card p-4`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="font-sans">
          <h3 className="font-medium text-gray-100">{quest.name}</h3>
          {quest.description && (
            <p className="mt-1 text-sm text-gray-400">{quest.description}</p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-gray-500">
            <span>{typeLabels[quest.quest_type]}</span>
            {(statName || statName2) && (
              <span>· {[statName, statName2].filter(Boolean).join(' + ')}</span>
            )}
            {isScheduledHabit && (
              <span>
                · {quest.scheduled_days.map((d) => WEEKDAY_LABELS[d]).join('/')}
              </span>
            )}
            {isScheduledHabit && quest.current_streak > 0 && (
              <span className="flex items-center gap-1 text-orange-400">
                <Fire width={14} height={14} />
                серия {quest.current_streak}
                {quest.best_streak > quest.current_streak && ` (рекорд ${quest.best_streak})`}
              </span>
            )}
            {quest.date_end && (
              <span>· до {new Date(quest.date_end).toLocaleString('ru-RU')}</span>
            )}
            <span className="flex items-center gap-1 text-yellow-500">
              <Coins width={14} height={14} />+{quest.reward_currency}
            </span>
            <span className="text-cyber-secondary">+{quest.reward_xp} XP</span>
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:shrink-0 sm:flex-row">
          {canComplete && (
            <Button
              variant="accent"
              onClick={() => complete(quest.id)}
              disabled={completing}
              className="w-full sm:w-auto"
            >
              Выполнить
            </Button>
          )}
          {doneToday && (
            <span className="self-center text-sm text-cyber-accent">Сделано сегодня</span>
          )}
          <Button variant="ghost" onClick={() => setIsEditing(true)} className="w-full sm:w-auto">
            Изменить
          </Button>
          <Button
            variant="ghost"
            onClick={() => remove(quest.id)}
            disabled={deleting}
            className="w-full sm:w-auto"
          >
            Удалить
          </Button>
        </div>
      </div>
    </div>
  )
}
