import { useState } from 'react'
import { usePurchaseReward, useDeleteReward, useUpdateReward } from '../hooks/useRewards'
import Button from './Button'

export default function RewardCard({ reward, currencyBalance }) {
  const [isEditing, setIsEditing] = useState(false)
  const [title, setTitle] = useState(reward.title)
  const [description, setDescription] = useState(reward.description ?? '')
  const [cost, setCost] = useState(String(reward.cost))
  const [unlockLevel, setUnlockLevel] = useState(String(reward.unlock_level))

  const { mutate: purchase, isPending: purchasing } = usePurchaseReward()
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
        className="space-y-2 rounded-lg border border-cyber-secondary bg-cyber-card p-4"
      >
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-sm text-gray-100"
          required
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        />
        <div className="flex gap-3">
          <input
            type="number"
            min="1"
            value={cost}
            onChange={(e) => setCost(e.target.value)}
            className="w-1/2 rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-sm text-gray-100"
            required
          />
          <input
            type="number"
            min="0"
            value={unlockLevel}
            onChange={(e) => setUnlockLevel(e.target.value)}
            className="w-1/2 rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-sm text-gray-100"
          />
        </div>

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
    <div
      className={`rounded-lg border p-4 ${
        reward.is_unlocked ? 'border-cyber-border bg-cyber-card' : 'border-cyber-border bg-cyber-card/50 opacity-60'
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
          <Button variant="accent" onClick={() => purchase(reward.id)} disabled={!canBuy || purchasing}>
            {buttonLabel}
          </Button>
          {!reward.is_purchased && (
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={() => setIsEditing(true)}>
                Изменить
              </Button>
              <Button variant="ghost" size="sm" onClick={() => remove(reward.id)} disabled={deleting}>
                Удалить
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
