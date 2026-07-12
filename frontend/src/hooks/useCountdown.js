import { useEffect, useState } from 'react'

// Ticks down to `targetDate` every second. Pass null/undefined to disable (returns 0).
export function useCountdown(targetDate) {
  const [remainingMs, setRemainingMs] = useState(() => (targetDate ? targetDate - Date.now() : 0))

  useEffect(() => {
    if (!targetDate) return
    const tick = () => setRemainingMs(Math.max(0, targetDate - Date.now()))
    tick()
    const interval = setInterval(tick, 1000)
    return () => clearInterval(interval)
  }, [targetDate])

  // targetDate can flip to null outside of the ticking effect (e.g. a fresh
  // server refetch reports the window open before our own tick catches up) —
  // reflect that immediately during render rather than waiting a second.
  if (!targetDate && remainingMs !== 0) {
    setRemainingMs(0)
  }

  return remainingMs
}

export function formatDuration(ms) {
  const totalSeconds = Math.floor(ms / 1000)
  const h = String(Math.floor(totalSeconds / 3600)).padStart(2, '0')
  const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, '0')
  const s = String(totalSeconds % 60).padStart(2, '0')
  return `${h}:${m}:${s}`
}
