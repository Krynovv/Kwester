import { useState } from 'react'
import { useCreateQuest } from '../hooks/useQuests'
import { useStats } from '../hooks/useStats'
import { fromDatetimeLocalValue } from '../utils/datetime'
import Button from './Button'

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

  const { data: stats } = useStats()
  const { mutate, isPending, error } = useCreateQuest()

  const handleSubmit = (e) => {
    e.preventDefault()
    mutate(
      {
        name,
        description: description || null,
        quest_type: questType,
        stat_id: statId ? Number(statId) : null,
        date_end: fromDatetimeLocalValue(dateEnd),
      },
      {
        onSuccess: () => {
          setName('')
          setDescription('')
          setQuestType('once')
          setStatId('')
          setDateEnd('')
        },
      }
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3 rounded-lg border border-cyber-border bg-cyber-card p-4"
    >
      <h2 className="font-display text-sm text-gray-300">НОВЫЙ КВЕСТ</h2>

      <input
        type="text"
        placeholder="Название"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="w-full rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        required
      />
      <textarea
        placeholder="Описание (необязательно)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="w-full rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        rows={2}
      />

      <div className="flex flex-wrap gap-3">
        <select
          value={questType}
          onChange={(e) => setQuestType(e.target.value)}
          className="rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        >
          {questTypes.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>

        <select
          value={statId}
          onChange={(e) => setStatId(e.target.value)}
          className="rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        >
          <option value="">Без привязки к стату</option>
          {stats?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>

        <input
          type="datetime-local"
          value={dateEnd}
          onChange={(e) => setDateEnd(e.target.value)}
          className="rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-sm text-gray-100"
          title="Дедлайн (необязательно)"
        />
      </div>

      {error && <p className="text-sm text-cyber-danger">Не удалось создать квест</p>}

      <Button type="submit" variant="primary" disabled={isPending}>
        {isPending ? 'Создаём...' : 'Создать квест'}
      </Button>
    </form>
  )
}
