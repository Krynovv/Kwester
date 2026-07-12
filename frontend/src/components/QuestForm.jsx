import { useState } from 'react'
import { Clock } from 'pixelarticons/react'
import { useCreateQuest } from '../hooks/useQuests'
import { useStats } from '../hooks/useStats'
import { fromDateAndTimeInputValue } from '../utils/datetime'
import Button from './Button'
import Select from './Select'

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
  const [dateEnd, setDateEnd] = useState('')
  const [timeEnd, setTimeEnd] = useState('')

  const { data: stats } = useStats()
  const { mutate, isPending, error } = useCreateQuest()

  const statOptions = [
    { value: '', label: 'Без привязки к стату' },
    ...(stats ?? []).map((s) => ({ value: String(s.id), label: s.name })),
  ]

  const handleSubmit = (e) => {
    e.preventDefault()
    mutate(
      {
        name,
        description: description || null,
        quest_type: questType,
        stat_id: statId ? Number(statId) : null,
        date_end: fromDateAndTimeInputValue(dateEnd, timeEnd),
      },
      {
        onSuccess: () => {
          setName('')
          setDescription('')
          setQuestType('once')
          setStatId('')
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

      <input
        type="text"
        placeholder="Название"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="w-full rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        required
      />
      <textarea
        placeholder="Описание (необязательно)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="w-full rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        rows={2}
      />

      <div className="flex flex-wrap items-center gap-3">
        <Select value={questType} onChange={setQuestType} options={questTypes} className="w-44" />
        <Select value={statId} onChange={setStatId} options={statOptions} className="w-52" />

        <input
          type="date"
          value={dateEnd}
          onChange={(e) => setDateEnd(e.target.value)}
          className="rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
          title="Дедлайн — дата (необязательно)"
        />
        <div
          className={`flex items-center gap-1 bg-cyber-muted px-2 ${!dateEnd ? 'opacity-40' : ''}`}
        >
          <Clock width={16} height={16} className="shrink-0 text-gray-500" />
          <input
            type="time"
            value={timeEnd}
            onChange={(e) => setTimeEnd(e.target.value)}
            disabled={!dateEnd}
            className="bg-transparent py-2 text-sm text-gray-100"
            title="Дедлайн — время (необязательно, по умолчанию конец дня)"
          />
        </div>

        <Button type="submit" variant="primary" disabled={isPending} className="ml-auto">
          {isPending ? 'Создаём...' : 'Создать квест'}
        </Button>
      </div>

      {error && <p className="text-sm text-cyber-danger">Не удалось создать квест</p>}
    </form>
  )
}
