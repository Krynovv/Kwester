import { useQuery } from '@tanstack/react-query'
import { fetchMe } from '../api/auth'
import { useShopItems } from '../hooks/useShop'
import ShopItemCard from '../components/ShopItemCard'

export default function ShopPage() {
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: fetchMe })
  const { data: items, isLoading } = useShopItems()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-lg text-gray-100">МАГАЗИН БОССА</h1>
        <p className="mt-1 text-sm text-gray-500">
          Тратится особая валюта, заработанная за победы над боссом.
        </p>
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
