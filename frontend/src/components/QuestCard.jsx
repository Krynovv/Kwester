import { useCompleteQuest, useDeleteQuest } from '../hooks/useQuests'

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
  const { mutate: complete, isPending: completing } = useCompleteQuest()
  const { mutate: remove, isPending: deleting } = useDeleteQuest()

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
