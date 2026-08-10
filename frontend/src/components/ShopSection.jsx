import ShopItemCard from './ShopItemCard'
import { CATEGORY_ACCENT, CATEGORY_LABEL } from '../constants/shopCategory'

export default function ShopSection({ title, description, items, bossCurrencyBalance, showCategoryLegend }) {
  if (items.length === 0) return null

  return (
    <div className="space-y-3">
      <div>
        <h2 className="font-display text-sm text-gray-200">{title.toUpperCase()}</h2>
        <p className="mt-1 text-sm text-gray-500">{description}</p>
        {showCategoryLegend && (
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-gray-500">
            <span>Цвет рамки — категория:</span>
            {Object.entries(CATEGORY_LABEL).map(([category, label]) => (
              <span key={category} className="flex items-center gap-1.5">
                <span
                  className="inline-block h-2 w-2"
                  style={{ backgroundColor: CATEGORY_ACCENT[category] }}
                />
                {label}
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {items.map((item) => (
          <ShopItemCard key={item.key} item={item} bossCurrencyBalance={bossCurrencyBalance} />
        ))}
      </div>
    </div>
  )
}
