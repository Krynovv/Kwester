import { useQuery } from '@tanstack/react-query'
import { Sword } from 'pixelarticons/react'
import { fetchMe } from '../api/auth'
import { useShopItems } from '../hooks/useShop'
import ShopItemCard from '../components/ShopItemCard'

export default function ShopPage() {
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: fetchMe })
  const { data: items, isLoading } = useShopItems()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="font-display text-lg text-gray-100">МАГАЗИН БОССА</h1>
          <p className="mt-1 text-sm text-gray-500">
            Тратится особая валюта, заработанная за победы над боссом.
          </p>
        </div>
        <span className="flex shrink-0 items-center gap-2 rounded-none border-2 border-cyber-secondary bg-cyber-bg px-3 py-1.5 text-cyber-secondary pixel-shadow-secondary">
          <Sword width={18} height={18} />
          {user?.boss_currency_balance ?? 0}
        </span>
      </div>

      {isLoading ? (
        <p className="text-gray-400">Загрузка...</p>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <ShopItemCard
              key={item.key}
              item={item}
              bossCurrencyBalance={user?.boss_currency_balance ?? 0}
            />
          ))}
        </div>
      )}
    </div>
  )
}
