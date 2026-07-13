export const statInfo = {
  Сила: {
    role: 'strength',
    description: 'Единственный источник урона по боссу.',
    formula: 'damage = strength.level × distinct_stats_completed_today',
    implemented: true,
  },
  Здоровье: {
    role: 'health',
    description: 'Определяет максимум HP игрока.',
    formula: 'max_hp = 100 + health.level × 10',
    implemented: true,
  },
  Интелект: {
    role: 'intellect',
    description: 'Бонус к награде за победу над боссом.',
    formula: '+2 особой валюты за каждый уровень',
    implemented: true,
  },
  Фокус: {
    role: 'focus',
    description: 'Задумано как рост шанса крита в бою с боссом.',
    formula: null,
    implemented: false,
  },
  Ловкость: {
    role: 'agility',
    description: 'Задумано как шанс уклонения от удара босса.',
    formula: null,
    implemented: false,
  },
}
