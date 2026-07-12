import { useState } from 'react'
import { usePurchaseReward, useDeleteReward, useUpdateReward } from '../hooks/useRewards'

export default function RewardCard({ reward, currencyBalance }) {
  const [isEditing, setIsEditing] = useState(false)
  const [title, setTitle] = useState(reward.title)
  const [description, setDescription] = useState(reward.description ?? '')
  const [cost, setCost] = useState(String(reward.cost))
  const [unlockLevel, setUnlockLevel] = useState(String(reward.unlock_level))

  const { mutate: purchase, isPending: purchasing, error } = usePurchaseReward()
  const { mutate: remove, isPending: deleting } = useDeleteReward()
  const { mutate: update, isPending: updating, error: updateError } = useUpdateReward()

  const canAfford = currencyBalance >= reward.cost
  const canBuy = reward.is_unlocked && !reward.is_purchased && canAfford

  let buttonLabel = 'Купить'
  if (purchasing) buttonLabel = 'Покупаем...'
  else if (reward.is_purchased) buttonLabel = 'Куплено'
  else if (!reward.is_unlocked) buttonLabel = `Откроется на ${reward.unlock_level} ур.`
  else if (!canAfford) buttonLabel = 'Не хватает валюты'

  const handleSave = (e) => {
    e.preventDefault()
    update(
      {
        id: reward.id,
        data: {
          title,
          description: description || null,
          cost: Number(cost),
          unlock_level: Number(unlockLevel) || 0,
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
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
          required
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
        />
        <div className="flex gap-3">
          <input
            type="number"
            min="1"
            value={cost}
            onChange={(e) => setCost(e.target.value)}
            className="w-1/2 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
            required
          />
          <input
            type="number"
            min="0"
            value={unlockLevel}
            onChange={(e) => setUnlockLevel(e.target.value)}
            className="w-1/2 rounded border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100"
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
    <div
      className={`rounded-lg border p-4 ${
        reward.is_unlocked ? 'border-gray-700 bg-gray-900' : 'border-gray-800 bg-gray-900/50 opacity-60'
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-medium text-gray-100">{reward.title}</h3>
          {reward.description && (
            <p className="mt-1 text-sm text-gray-400">{reward.description}</p>
          )}
          <p className="mt-2 text-sm text-yellow-500">{reward.cost} 🪙</p>
        </div>

        <div className="flex shrink-0 flex-col items-end gap-2">
          <button
            onClick={() => purchase(reward.id)}
            disabled={!canBuy || purchasing}
            className="rounded bg-purple-600 px-3 py-1 text-sm text-white disabled:opacity-40"
          >
            {buttonLabel}
          </button>
          {!reward.is_purchased && (
            <div className="flex gap-2">
              <button
                onClick={() => setIsEditing(true)}
                className="text-xs text-gray-500"
              >
                Изменить
              </button>
              <button
                onClick={() => remove(reward.id)}
                disabled={deleting}
                className="text-xs text-gray-500 disabled:opacity-40"
              >
                Удалить
              </button>
            </div>
          )}
        </div>
      </div>
      {error && <p className="mt-2 text-sm text-red-400">Не удалось купить</p>}
    </div>
  )
}
