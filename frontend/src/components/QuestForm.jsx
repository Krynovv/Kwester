import { useState } from 'react'
import { useCreateQuest } from '../hooks/useQuests'
import { useStats } from '../hooks/useStats'

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
      },
      {
        onSuccess: () => {
          setName('')
          setDescription('')
          setQuestType('once')
          setStatId('')
        },
      }
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3 rounded-lg border border-gray-800 bg-gray-900 p-4"
    >
      <h2 className="text-sm font-medium text-gray-300">Новый квест</h2>

      <input
        type="text"
        placeholder="Название"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
        required
      />
      <textarea
        placeholder="Описание (необязательно)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
        rows={2}
      />

      <div className="flex gap-3">
        <select
          value={questType}
          onChange={(e) => setQuestType(e.target.value)}
          className="rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
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
          className="rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
        >
          <option value="">Без привязки к стату</option>
          {stats?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="text-sm text-red-400">Не удалось создать квест</p>}

      <button
        type="submit"
        disabled={isPending}
        className="rounded bg-purple-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
      >
        {isPending ? 'Создаём...' : 'Создать квест'}
      </button>
    </form>
  )
}
