import { useEffect, useState } from 'react'
import { useToastStore } from '../store/toastStore'

// Общая логика для StatsOverview/StatsRingRow: следит за ростом level у
// статов и коротко подсвечивает те, что только что повысились (плюс тост).
export function useLevelUpToasts(stats) {
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

  return leveledUpIds
}
