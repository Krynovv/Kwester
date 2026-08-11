import { useState } from 'react'
import { Coins } from 'pixelarticons/react'
import { usePurchaseReward, useDeleteReward, useUpdateReward } from '../hooks/useRewards'
import Button from './Button'
import HoldToDeleteButton from './HoldToDeleteButton'

export default function RewardCard({ reward, currencyBalance }) {
  const [isEditing, setIsEditing] = useState(false)
  const [title, setTitle] = useState(reward.title)
  const [description, setDescription] = useState(reward.description ?? '')
  const [cost, setCost] = useState(String(reward.cost))
  const [unlockLevel, setUnlockLevel] = useState(String(reward.unlock_level))
  const [repeatable, setRepeatable] = useState(reward.repeatable)

  const { mutate: purchase, isPending: purchasing } = usePurchaseReward()
  const { mutate: remove, isPending: deleting } = useDeleteReward()
  const { mutate: update, isPending: updating, error: updateError } = useUpdateReward()

  const canAfford = currencyBalance >= reward.cost
  const locked = reward.is_purchased && !reward.repeatable
  const canBuy = reward.is_unlocked && !locked && canAfford

  let buttonLabel = reward.repeatable && reward.purchase_count > 0 ? 'Купить ещё' : 'Купить'
  if (purchasing) buttonLabel = 'Покупаем...'
  else if (!reward.is_unlocked) buttonLabel = `Откроется на ${reward.unlock_level} ур.`
  else if (locked) buttonLabel = 'Куплено'
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
          repeatable,
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

        <label className="flex cursor-pointer items-center gap-2 text-sm text-gray-300 select-none">
          <span className="cyber-checkbox">
            <input
              type="checkbox"
              checked={repeatable}
              onChange={(e) => setRepeatable(e.target.checked)}
            />
            <span className="cyber-checkbox-fill" />
          </span>
          Можно покупать многократно
        </label>

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
          <p className="mt-2 flex items-center gap-2 text-sm text-yellow-500">
            <span className="flex items-center gap-1">
              <Coins width={14} height={14} />
              {reward.cost}
            </span>
            {reward.repeatable && reward.purchase_count > 0 && (
              <span className="text-gray-500">· куплено {reward.purchase_count}×</span>
            )}
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
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" className="flex-1 sm:flex-none" onClick={() => setIsEditing(true)}>
              Изменить
            </Button>
            <HoldToDeleteButton
              size="sm"
              className="flex-1 sm:flex-none"
              onConfirm={() => remove(reward.id)}
              disabled={deleting}
            >
              Удалить
            </HoldToDeleteButton>
          </div>
        </div>
      </div>
    </div>
  )
}
