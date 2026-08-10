import ShopItemCard from './ShopItemCard'

export default function ShopSection({ title, description, items, bossCurrencyBalance }) {
  if (items.length === 0) return null

  return (
    <div className="space-y-3">
      <div>
        <h2 className="font-display text-sm text-gray-200">{title.toUpperCase()}</h2>
        <p className="mt-1 text-sm text-gray-500">{description}</p>
      </div>
      {items.map((item) => (
        <ShopItemCard key={item.key} item={item} bossCurrencyBalance={bossCurrencyBalance} />
      ))}
    </div>
  )
}
