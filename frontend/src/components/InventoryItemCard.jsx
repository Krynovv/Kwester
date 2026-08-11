import { Sparkle, Check } from 'pixelarticons/react'
import { ITEM_ICONS, accentFor } from '../constants/itemStyle'

// Упрощённая версия ShopItemCard — без переворота и описания, только
// иконка/название/количество. Три режима поведения карточки:
// - armable: расходники с категорией (см. FIGHT_CONSUMABLE_KEYS на
//   бэкенде) — тап армирует их на следующий бой (POST /boss/fight).
// - usable: heal_100 — тап сразу применяет эффект через POST
//   /shop/{key}/use (пьётся, когда реально нужно, а не при покупке).
// - иначе — постоянные предметы и extra_boss_fight: не кликабельны.
export default function InventoryItemCard({ item, armable, armed, onToggleArm, usable, onUse, isUsing }) {
  const Icon = ITEM_ICONS[item.key] ?? Sparkle
  const accent = accentFor(item)
  const interactive = armable || usable

  // Слева — остаток зарядов (постоянным предметам нечего показывать, у них
  // нет счётчика). Справа — индикатор действия: галочка вместо текста —
  // пустая рамка/закрашенная для armable (тоггл "в бою"), всегда закрашенная
  // для постоянных (они пассивны и всегда "включены"), текст — только для
  // usable (это не тоггл, а разовое действие, галочка тут вводила бы в
  // заблуждение).
  const quantityBadge = item.permanent ? (
    <span />
  ) : (
    <span
      className="shrink-0 border px-1 py-0.5 text-[9px] whitespace-nowrap"
      style={{ color: accent, borderColor: accent }}
    >
      ×{item.owned_charges}
    </span>
  )

  let actionBadge = <span />
  if (item.permanent) {
    // Постоянные предметы всегда "включены" — тот же чекбокс, сразу в
    // заполненном виде (галочка нужна: заливка тут не переключается кликом,
    // без неё квадрат было бы не отличить от чистого декора).
    actionBadge = (
      <span
        className="flex h-3 w-3 shrink-0 items-center justify-center border-2"
        style={{ borderColor: accent, backgroundColor: accent }}
      >
        <Check width={8} height={8} className="text-cyber-bg" />
      </span>
    )
  } else if (armable) {
    // Тот же квадратный чекбокс, что и в форме наград (uiverse.io/arthur_6104/sharp-puma-27):
    // пустая рамка -> сплошная заливка при "в бою", цветом самого предмета
    // (не единым cyber-secondary — иначе все выбранные предметы сливаются
    // в один цвет и перестаёт быть видно, какой именно взят).
    actionBadge = (
      <span
        className="h-3 w-3 shrink-0 border-2"
        style={{ borderColor: accent, backgroundColor: armed ? accent : 'transparent' }}
      />
    )
  } else if (usable) {
    actionBadge = (
      <span
        className="shrink-0 border px-1 py-0.5 text-[9px] whitespace-nowrap uppercase"
        style={{ color: accent, borderColor: accent }}
      >
        {isUsing ? '...' : 'выпить'}
      </span>
    )
  }

  const content = (
    <>
      <div className="flex justify-between gap-1 p-1.5">
        {quantityBadge}
        {actionBadge}
      </div>

      <div className="flex min-h-0 flex-1 items-center justify-center overflow-hidden">
        <Icon width={28} height={28} style={{ color: accent }} />
      </div>

      <div className="border-t-2 border-cyber-border p-1.5">
        <div className="font-display text-[8px] leading-snug text-gray-100">{item.name}</div>
      </div>
    </>
  )

  const boxShadow = `6px 6px 0 0 ${accent}`

  if (!interactive) {
    return (
      <div
        className="flex aspect-[3/4] min-h-0 min-w-0 flex-col border-2 border-cyber-border bg-cyber-card"
        style={{ boxShadow }}
      >
        {content}
      </div>
    )
  }

  const handleClick = armable ? onToggleArm : onUse
  const ariaLabel = `${item.name} — ${armable ? 'взять в бой' : 'использовать'}`

  return (
    <div
      role="button"
      tabIndex={0}
      aria-pressed={armable ? armed : undefined}
      aria-disabled={usable ? isUsing : undefined}
      aria-label={ariaLabel}
      onClick={usable && isUsing ? undefined : handleClick}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !(usable && isUsing)) {
          e.preventDefault()
          handleClick()
        }
      }}
      className={`flex aspect-[3/4] min-h-0 min-w-0 flex-col border-2 bg-cyber-card ${
        usable && isUsing ? 'cursor-wait opacity-70' : 'cursor-pointer'
      }`}
      style={{ boxShadow, borderColor: armed ? accent : 'var(--color-cyber-border)' }}
    >
      {content}
    </div>
  )
}
