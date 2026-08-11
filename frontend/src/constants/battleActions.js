import { Sword, Laugh, Comment } from 'pixelarticons/react'

// Соответствует PlayerAction на бэкенде (service/combat.py). Общий
// источник для панели действий/пузырьков чата (BossChatPage) и
// объяснения на экране подготовки к бою (BossFightPage).
export const ACTIONS = [
  {
    value: 'attack', label: 'Атака', icon: Sword, accent: 'var(--color-cyber-primary)',
    hint: 'Сила — полный урон',
  },
  {
    value: 'joke', label: 'Шутка', icon: Laugh, accent: 'var(--color-cyber-secondary)',
    hint: 'Интеллект — урона меньше, но вдвое выше крит; крит затыкает босса',
  },
  {
    value: 'excuse', label: 'Отговорка', icon: Comment, accent: 'var(--color-cyber-accent)',
    hint: 'Ловкость — без урона, зато х2 уклонение от ответа босса',
  },
]
