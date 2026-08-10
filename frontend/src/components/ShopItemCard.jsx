import { useState } from 'react'
import {
  Coins, Heart, Sword, Fire, Shield, Sparkle, Reload, Clock, Eye, Handbag,
  HumanArmsUp, Target, SpeedFast, Lightbulb, Thermometer,
} from 'pixelarticons/react'
import { usePurchaseShopItem } from '../hooks/useShop'
import Button from './Button'

const ITEM_ICONS = {
  heal_100: Heart,
  extra_boss_fight: Sword,
  potion_rage: Fire,
  potion_guard: Shield,
  charm_mercy: Sparkle,
  token_second_chance: Reload,
  token_patience: Clock,
  eye_focus: Eye,
  bag: Handbag,
  spec_strength: HumanArmsUp,
  spec_focus: Target,
  spec_agility: SpeedFast,
  spec_intellect: Lightbulb,
  spec_health: Thermometer,
}

// offensive/defensive/outcome — категории расходников из shop-design.md.
// permanent-предметы категории не имеют (category: null) — красим золотом.
const CATEGORY_ACCENT = {
  offensive: 'var(--color-cyber-primary)',
  defensive: 'var(--color-cyber-secondary)',
  outcome: 'var(--color-cyber-accent)',
}

function accentFor(item) {
  if (item.permanent) return 'var(--color-cyber-gold)'
  return CATEGORY_ACCENT[item.category] ?? 'var(--color-cyber-secondary)'
}

export default function ShopItemCard({ item, bossCurrencyBalance }) {
  const [flipped, setFlipped] = useState(false)
  const { mutate: purchase, isPending } = usePurchaseShopItem()

  // Гейт по уровню персонажа временно не показываем в UI (бэкенд всё равно
  // отклонит покупку 400-й, если предмет не разблокирован) — до
  // отдельного решения по тому, как это подавать.
  const alreadyOwned = !item.repeatable && item.owned_charges > 0
  const canAfford = bossCurrencyBalance >= item.cost
  const canBuy = canAfford && !alreadyOwned

  let buttonLabel = `Купить · ${item.cost}`
  if (isPending) buttonLabel = 'Покупаем...'
  else if (alreadyOwned) buttonLabel = 'Куплено'
  else if (!canAfford) buttonLabel = 'Не хватает валюты'

  const Icon = ITEM_ICONS[item.key] ?? Sparkle
  const accent = accentFor(item)
  const toggle = () => setFlipped((f) => !f)

  return (
    <div
      role="button"
      tabIndex={0}
      aria-pressed={flipped}
      aria-label={`${item.name} — подробнее`}
      onClick={toggle}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          toggle()
        }
      }}
      className={`flip-card aspect-[3/4] min-w-0 cursor-pointer ${flipped ? 'is-flipped' : ''}`}
      style={{ '--flip-accent': accent }}
    >
      <div className="flip-card-inner">
        <div
          className="flip-card-face flex flex-col border-2 border-cyber-border bg-cyber-card"
          style={{ boxShadow: `6px 6px 0 0 ${accent}` }}
        >
          <div className="flex items-start justify-between gap-2 p-2.5">
            <span
              className="shrink-0 border px-1.5 py-0.5 text-xs whitespace-nowrap uppercase tracking-wide"
              style={{ color: accent, borderColor: accent }}
            >
              {item.permanent ? 'постоянный' : 'расходник'}
            </span>
            <span className="flex shrink-0 items-center gap-1 text-sm text-cyber-gold">
              <Coins width={14} height={14} />
              {item.cost}
            </span>
          </div>

          <div className="relative grid flex-1 place-items-center">
            <div
              className="absolute h-16 w-16 rounded-full opacity-40 blur-2xl"
              style={{ backgroundColor: accent }}
            />
            <Icon width={44} height={44} style={{ color: accent }} className="relative" />
          </div>

          <div className="border-t-2 border-cyber-border p-2.5">
            <div className="font-display text-[10px] leading-relaxed text-gray-100">{item.name}</div>
            <div className="mt-1.5 flex items-center gap-1 text-xs text-gray-500">
              <Clock width={12} height={12} className="opacity-70" />
              тап — детали
            </div>
          </div>
        </div>

        <div className="flip-card-back flip-card-face flex flex-col p-3">
          <div className="relative z-1 flex h-full flex-col gap-2">
            <div className="font-display text-[11px] leading-relaxed" style={{ color: accent }}>
              {item.name}
            </div>
            <p className="flip-card-desc flex-1 text-sm text-gray-200">{item.description}</p>
            <Button
              variant="primary"
              onClick={(e) => {
                e.stopPropagation()
                purchase(item.key)
              }}
              disabled={!canBuy || isPending}
              className="w-full shrink-0"
              style={{ backgroundColor: accent, boxShadow: '4px 4px 0 0 #000' }}
            >
              {buttonLabel}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
