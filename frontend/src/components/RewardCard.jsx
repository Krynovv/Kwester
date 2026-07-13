import { useState } from 'react'
import { Coins } from 'pixelarticons/react'
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
        className="space-y-2 rounded-none border-2 border-cyber-secondary bg-cyber-card p-4"
      >
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
          required
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        />
        <div className="flex gap-3">
          <input
            type="number"
            min="1"
            value={cost}
            onChange={(e) => setCost(e.target.value)}
            className="w-1/2 rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
            required
          />
          <input
            type="number"
            min="0"
            value={unlockLevel}
            onChange={(e) => setUnlockLevel(e.target.value)}
            className="w-1/2 rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
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
      className={`rounded-none border-2 p-4 ${
        reward.is_unlocked ? 'border-cyber-border bg-cyber-card' : 'border-cyber-border bg-cyber-card/50 opacity-60'
      }`}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="font-medium text-gray-100">{reward.title}</h3>
          {reward.description && (
            <p className="mt-1 text-sm text-gray-400">{reward.description}</p>
          )}
          <p className="mt-2 flex items-center gap-1 text-sm text-yellow-500">
            <Coins width={14} height={14} />
            {reward.cost}
          </p>
        </div>

        <div className="flex flex-col gap-2 sm:shrink-0 sm:items-end">
          <Button
            variant="accent"
            onClick={() => purchase(reward.id)}
            disabled={!canBuy || purchasing}
            className="w-full sm:w-auto"
          >
            {buttonLabel}
          </Button>
          {!reward.is_purchased && (
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" className="flex-1 sm:flex-none" onClick={() => setIsEditing(true)}>
                Изменить
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="flex-1 sm:flex-none"
                onClick={() => remove(reward.id)}
                disabled={deleting}
              >
                Удалить
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
