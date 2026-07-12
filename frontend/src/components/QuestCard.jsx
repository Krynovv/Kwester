import { useState } from 'react'
import { useCompleteQuest, useDeleteQuest, useUpdateQuest } from '../hooks/useQuests'
import { useStats } from '../hooks/useStats'
import { toDatetimeLocalValue, fromDatetimeLocalValue } from '../utils/datetime'

const typeLabels = {
  once: 'Разовый',
  daily: 'Ежедневный',
  weekly: 'Еженедельный',
  habit: 'Привычка',
}

const statusBorder = {
  active: 'border-gray-700',
  done: 'border-green-700 opacity-60',
  failed: 'border-red-800 opacity-60',
}

export default function QuestCard({ quest, statName }) {
  const [isEditing, setIsEditing] = useState(false)
  const [name, setName] = useState(quest.name)
  const [description, setDescription] = useState(quest.description ?? '')
  const [statId, setStatId] = useState(quest.stat_id ?? '')
  const [dateEnd, setDateEnd] = useState(toDatetimeLocalValue(quest.date_end))

  const { data: stats } = useStats()
  const { mutate: complete, isPending: completing } = useCompleteQuest()
  const { mutate: remove, isPending: deleting } = useDeleteQuest()
  const { mutate: update, isPending: updating, error: updateError } = useUpdateQuest()

  const handleSave = (e) => {
    e.preventDefault()
    update(
      {
        id: quest.id,
        data: {
          name,
          description: description || null,
          stat_id: statId ? Number(statId) : null,
          date_end: fromDatetimeLocalValue(dateEnd),
        },
      },
      { onSuccess: () => setIsEditing(false) }
    )
  }

  if (isEditing) {
    return (
      <form
        onSubmit={handleSave}
        className="space-y-2 rounded-lg border border-purple-700 bg-gray-900 p-4"
      >
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
          required
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
        />
        <div className="flex flex-wrap gap-3">
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
          <input
            type="datetime-local"
            value={dateEnd}
            onChange={(e) => setDateEnd(e.target.value)}
            className="rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
          />
        </div>

        {updateError && <p className="text-sm text-red-400">Не удалось сохранить</p>}

        <div className="flex gap-2">
          <button
            type="submit"
            disabled={updating}
            className="rounded bg-purple-600 px-3 py-1 text-sm text-white disabled:opacity-50"
          >
            {updating ? 'Сохраняем...' : 'Сохранить'}
          </button>
          <button
            type="button"
            onClick={() => setIsEditing(false)}
            className="rounded bg-gray-800 px-3 py-1 text-sm text-gray-300"
          >
            Отмена
          </button>
        </div>
      </form>
    )
  }

  return (
    <div className={`rounded-lg border ${statusBorder[quest.status]} bg-gray-900 p-4`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-medium text-gray-100">{quest.name}</h3>
          {quest.description && (
            <p className="mt-1 text-sm text-gray-400">{quest.description}</p>
          )}
          <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-500">
            <span>{typeLabels[quest.quest_type]}</span>
            {statName && <span>· {statName}</span>}
            {quest.date_end && (
              <span>· до {new Date(quest.date_end).toLocaleString('ru-RU')}</span>
            )}
            <span className="text-yellow-500">+{quest.reward_currency} 🪙</span>
            <span className="text-purple-400">+{quest.reward_xp} XP</span>
          </div>
        </div>

        <div className="flex shrink-0 gap-2">
          {quest.status === 'active' && (
            <button
              onClick={() => complete(quest.id)}
              disabled={completing}
              className="rounded bg-purple-600 px-3 py-1 text-sm text-white disabled:opacity-50"
            >
              Выполнить
            </button>
          )}
          <button
            onClick={() => setIsEditing(true)}
            className="rounded bg-gray-800 px-3 py-1 text-sm text-gray-300"
          >
            Изменить
          </button>
          <button
            onClick={() => remove(quest.id)}
            disabled={deleting}
            className="rounded bg-gray-800 px-3 py-1 text-sm text-gray-300 disabled:opacity-50"
          >
            Удалить
          </button>
        </div>
      </div>
    </div>
  )
}
