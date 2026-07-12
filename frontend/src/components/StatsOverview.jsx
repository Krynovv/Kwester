import { useEffect, useState } from 'react'
import { useStats } from '../hooks/useStats'
import { useToastStore } from '../store/toastStore'

const statColors = {
  Сила: { bar: 'bg-cyber-primary', text: 'text-cyber-primary' },
  Ловкость: { bar: 'bg-cyber-accent', text: 'text-cyber-accent' },
  Интелект: { bar: 'bg-cyber-secondary', text: 'text-cyber-secondary' },
  Фокус: { bar: 'bg-cyber-cyan', text: 'text-cyber-cyan' },
  Здоровье: { bar: 'bg-cyber-pink', text: 'text-cyber-pink' },
}
const defaultColor = { bar: 'bg-cyber-secondary', text: 'text-cyber-secondary' }

export default function StatsOverview() {
  const { data: stats, isLoading } = useStats()
  const addToast = useToastStore((state) => state.addToast)

  const [prevLevels, setPrevLevels] = useState({})
  const [leveledUpIds, setLeveledUpIds] = useState([])

  // Pure comparison against last render's levels, done during render itself
  // (React's recommended way to "adjust state when data changes" — no Effect needed for this part).
  if (stats) {
    const nextLevels = Object.fromEntries(stats.map((s) => [s.id, s.level]))
    const changed = stats.some((s) => nextLevels[s.id] !== prevLevels[s.id])
    if (changed) {
      const newlyLeveled = stats
        .filter((s) => prevLevels[s.id] !== undefined && s.level > prevLevels[s.id])
        .map((s) => s.id)
      setPrevLevels(nextLevels)
      setLeveledUpIds(newlyLeveled)
    }
  }

  // Impure side effects (toast + timed pulse reset) react to the detected level-ups.
  useEffect(() => {
    if (leveledUpIds.length === 0 || !stats) return
    for (const id of leveledUpIds) {
      const stat = stats.find((s) => s.id === id)
      if (stat) addToast(`«${stat.name}» повысил уровень: ${stat.level}!`, 'success')
    }
    const timer = setTimeout(() => setLeveledUpIds([]), 1000)
    return () => clearTimeout(timer)
  }, [leveledUpIds, stats, addToast])

  if (isLoading) return <p className="text-gray-400">Загрузка статов...</p>

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      {stats?.map((stat) => {
        const progress = Math.min(100, (stat.current_xp / stat.xp_to_next_level) * 100)
        const color = statColors[stat.name] ?? defaultColor
        return (
          <div
            key={stat.id}
            className={`rounded-lg border border-cyber-border bg-cyber-card p-3 ${
              leveledUpIds.includes(stat.id) ? 'animate-level-up' : ''
            }`}
          >
            <p className="text-sm text-gray-300">{stat.name}</p>
            <p className={`text-xs ${color.text}`}>Ур. {stat.level}</p>
            <div className="relative mt-2 h-2 overflow-hidden rounded-full bg-cyber-muted">
              <div
                className={`h-2 rounded-full ${color.bar} transition-all duration-500 ease-out`}
                style={{ width: `${progress}%` }}
              />
              <div className="bar-segments" />
            </div>
            <p className="mt-1 text-right text-[10px] text-gray-500">
              {stat.current_xp} / {stat.xp_to_next_level} XP
            </p>
          </div>
        )
      })}
    </div>
  )
}
