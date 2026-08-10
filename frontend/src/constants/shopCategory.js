// offensive/defensive/outcome — категории расходников из shop-design.md.
// permanent-предметы категории не имеют (category: null).
export const CATEGORY_ACCENT = {
  offensive: 'var(--color-cyber-primary)',
  defensive: 'var(--color-cyber-secondary)',
  outcome: 'var(--color-cyber-accent)',
}

export const CATEGORY_LABEL = {
  offensive: 'атака',
  defensive: 'защита',
  outcome: 'исход боя',
}

// Порядок групп при сортировке — как в легенде. Предметы без категории
// (heal_100, extra_boss_fight — не часть боевой категоризации из
// shop-design.md) уходят в свою группу в конце.
const CATEGORY_ORDER = ['offensive', 'defensive', 'outcome']

export function sortByCategory(items) {
  const rank = (item) => {
    const index = item.category ? CATEGORY_ORDER.indexOf(item.category) : -1
    return index === -1 ? CATEGORY_ORDER.length : index
  }
  // Array.prototype.sort стабилен (ES2019+) — предметы одной категории
  // сохраняют исходный порядок между собой.
  return [...items].sort((a, b) => rank(a) - rank(b))
}
