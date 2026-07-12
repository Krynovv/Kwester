import { usePurchaseShopItem } from '../hooks/useShop'

export default function ShopItemCard({ item, bossCurrencyBalance }) {
  const { mutate: purchase, isPending, error } = usePurchaseShopItem()

  const canAfford = bossCurrencyBalance >= item.cost
  const canBuy = item.is_unlocked && canAfford

  let buttonLabel = 'Купить'
  if (isPending) buttonLabel = 'Покупаем...'
  else if (!item.is_unlocked) buttonLabel = `Откроется на ${item.unlock_level} ур. босса`
  else if (!canAfford) buttonLabel = 'Не хватает валюты'

  return (
    <div
      className={`rounded-lg border p-4 ${
        item.is_unlocked ? 'border-gray-700 bg-gray-900' : 'border-gray-800 bg-gray-900/50 opacity-60'
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="font-medium text-gray-100">{item.name}</h3>
          <p className="mt-1 text-sm text-gray-400">{item.description}</p>
          <div className="mt-2 flex items-center gap-3 text-sm">
            <span className="text-yellow-500">{item.cost} ⚔️</span>
            {item.owned_charges > 0 && (
              <span className="text-purple-400">Заряды: {item.owned_charges}</span>
            )}
          </div>
        </div>

        <button
          onClick={() => purchase(item.key)}
          disabled={!canBuy || isPending}
          className="shrink-0 rounded bg-red-700 px-3 py-1 text-sm text-white disabled:opacity-40"
        >
          {buttonLabel}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-400">Не удалось купить</p>}
    </div>
  )
}
