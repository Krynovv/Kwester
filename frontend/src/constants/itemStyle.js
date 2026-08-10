import {
  Heart, Sword, Fire, Shield, Sparkle, Reload, Clock, Eye, Handbag,
  HumanArmsUp, Target, SpeedFast, Lightbulb, Thermometer,
} from 'pixelarticons/react'
import { CATEGORY_ACCENT } from './shopCategory'

// Общая иконка/цвет предмета — используется и карточкой магазина, и
// карточкой инвентаря, чтобы один и тот же предмет выглядел одинаково
// в обоих местах.
export const ITEM_ICONS = {
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

// Предметы без категории делятся на два разных механизма — важно не путать
// их в UI:
// - heal_100 покупается про запас и пьётся вручную из инвентаря, когда
//   реально нужно (backend: USE_HANDLERS в service/shop.py).
// - extra_boss_fight списывается сам при старте боя сверх дневного лимита —
//   его нельзя ни взять в бой, ни выпить, поэтому в этот набор не входит.
export const USABLE_ITEM_KEYS = new Set(['heal_100'])

export function accentFor(item) {
  if (item.permanent) return 'var(--color-cyber-gold)'
  // heal_100/extra_boss_fight — расходники без категории (не входят в
  // offensive/defensive/outcome из shop-design.md). Красный, не cyan —
  // тот слишком похож на cyber-secondary ("защита") и путался с ней.
  return CATEGORY_ACCENT[item.category] ?? 'var(--color-cyber-danger)'
}
