// offensive/defensive/outcome — категории расходников из shop-design.md.
// permanent-предметы категории не имеют (category: null).
export const CATEGORY_ACCENT = {
  defensive: 'var(--color-cyber-secondary)',
  outcome: 'var(--color-cyber-accent)',
  offensive: 'var(--color-cyber-primary)',
}

// Порядок ключей ниже — порядок и легенды, и групп карточек.
export const CATEGORY_LABEL = {
  defensive: 'защита',
  outcome: 'исход боя',
  offensive: 'атака',
}

// Предметы без категории (heal_100, extra_boss_fight — не часть боевой
// категоризации из shop-design.md) уходят в свою группу в конце.
const CATEGORY_ORDER = Object.keys(CATEGORY_LABEL)

export function sortByCategory(items) {
  const rank = (item) => {
    const index = item.category ? CATEGORY_ORDER.indexOf(item.category) : -1
    return index === -1 ? CATEGORY_ORDER.length : index
  }
  return [...items].sort((a, b) => {
    const byCategory = rank(a) - rank(b)
    // Внутри категории — по цене (дешевле сначала); стабильный sort
    // сохраняет исходный порядок при равной цене.
    return byCategory !== 0 ? byCategory : a.cost - b.cost
  })
}
