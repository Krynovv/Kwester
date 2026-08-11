import { useQuery } from '@tanstack/react-query'
import { Sword } from 'pixelarticons/react'
import { fetchMe } from '../api/auth'
import { useShopItems } from '../hooks/useShop'
import { sortByCategory } from '../constants/shopCategory'
import ShopSection from '../components/ShopSection'

// Скрыто с витрины по просьбе — сам предмет и его эффект (доп. бой через
// заряд в service/fight.py) на бэкенде не трогали, только не показываем карточку.
const HIDDEN_ITEM_KEYS = new Set(['extra_boss_fight'])

export default function ShopPage() {
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: fetchMe })
  const { data: rawItems, isLoading } = useShopItems()
  const items = rawItems?.filter((item) => !HIDDEN_ITEM_KEYS.has(item.key))

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
            items={sortByCategory(items.filter((item) => !item.permanent))}
            bossCurrencyBalance={user?.boss_currency_balance ?? 0}
            showCategoryLegend
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
