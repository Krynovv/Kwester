import { usePurchaseReward, useDeleteReward } from '../hooks/useRewards'

export default function RewardCard({ reward, currencyBalance }) {
  const { mutate: purchase, isPending: purchasing, error } = usePurchaseReward()
  const { mutate: remove, isPending: deleting } = useDeleteReward()

  const canAfford = currencyBalance >= reward.cost
  const canBuy = reward.is_unlocked && !reward.is_purchased && canAfford

  let buttonLabel = 'Купить'
  if (purchasing) buttonLabel = 'Покупаем...'
  else if (reward.is_purchased) buttonLabel = 'Куплено'
  else if (!reward.is_unlocked) buttonLabel = `Откроется на ${reward.unlock_level} ур.`
  else if (!canAfford) buttonLabel = 'Не хватает валюты'

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
            <button
              onClick={() => remove(reward.id)}
              disabled={deleting}
              className="text-xs text-gray-500 disabled:opacity-40"
            >
              Удалить
            </button>
          )}
        </div>
      </div>
      {error && <p className="mt-2 text-sm text-red-400">Не удалось купить</p>}
    </div>
  )
}
