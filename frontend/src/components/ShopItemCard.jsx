import { Sword } from 'pixelarticons/react'
import { usePurchaseShopItem } from '../hooks/useShop'
import Button from './Button'

export default function ShopItemCard({ item, bossCurrencyBalance }) {
  const { mutate: purchase, isPending } = usePurchaseShopItem()

  // Гейт по уровню персонажа временно не показываем в UI (бэкенд всё равно
  // отклонит покупку 400-й, если предмет не разблокирован) — до
  // отдельного решения по тому, как это подавать.
  const alreadyOwned = !item.repeatable && item.owned_charges > 0
  const canAfford = bossCurrencyBalance >= item.cost
  const canBuy = canAfford && !alreadyOwned

  let buttonLabel = 'Купить'
  if (isPending) buttonLabel = 'Покупаем...'
  else if (alreadyOwned) buttonLabel = 'Куплено'
  else if (!canAfford) buttonLabel = 'Не хватает валюты'

  return (
    <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-4">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="font-medium text-gray-100">{item.name}</h3>
          <p className="mt-1 text-sm text-gray-400">{item.description}</p>
          <div className="mt-2 flex items-center gap-3 text-sm">
            <span className="flex items-center gap-1 text-cyber-secondary">
              <Sword width={16} height={16} />
              {item.cost}
            </span>
            {item.owned_charges > 0 && (
              <span className="text-cyber-accent">
                {item.permanent ? 'Куплено' : `Заряды: ${item.owned_charges}`}
              </span>
            )}
          </div>
        </div>

        <Button
          variant="primary"
          onClick={() => purchase(item.key)}
          disabled={!canBuy || isPending}
          className="w-full sm:w-auto sm:shrink-0"
        >
          {buttonLabel}
        </Button>
      </div>
    </div>
  )
}
