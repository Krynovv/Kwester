import { useQuery } from '@tanstack/react-query'
import { Sword } from 'pixelarticons/react'
import { fetchMe } from '../api/auth'
import { useShopItems } from '../hooks/useShop'
import ShopSection from '../components/ShopSection'

export default function ShopPage() {
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: fetchMe })
  const { data: items, isLoading } = useShopItems()

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-display text-lg text-gray-100">МАГАЗИН БОССА</h1>
          <span className="ml-auto flex shrink-0 items-center gap-2 rounded-none bg-cyber-bg px-3 py-1.5 text-cyber-secondary">
            <Sword width={18} height={18} />
            {user?.boss_currency_balance ?? 0}
          </span>
        </div>
        <p className="mt-3 text-sm text-gray-500">
          Тратится особая валюта, заработанная за победы над боссом.
        </p>
      </div>

      {isLoading ? (
        <p className="text-gray-400">Загрузка...</p>
      ) : (
        <>
          <ShopSection
            title="Расходники"
            description="Заряд списывается при выборе на конкретный бой."
            items={items.filter((item) => !item.permanent)}
            bossCurrencyBalance={user?.boss_currency_balance ?? 0}
          />
          <ShopSection
            title="Постоянные предметы"
            description="Покупаются один раз и действуют всегда."
            items={items.filter((item) => item.permanent)}
            bossCurrencyBalance={user?.boss_currency_balance ?? 0}
          />
        </>
      )}
    </div>
  )
}
