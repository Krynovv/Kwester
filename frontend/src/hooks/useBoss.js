import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchBossStatus, fightBoss } from '../api/boss'
import { useToastStore } from '../store/toastStore'

export function useBossStatus() {
  return useQuery({ queryKey: ['boss'], queryFn: fetchBossStatus })
}

// When can the player fight next? null means "right now".
// Returns an epoch-ms number, not a Date — callers put this straight into a
// useEffect dependency array (via useCountdown), and a fresh `new Date(...)`
// on every call would be a new reference each render even when the moment
// it represents hasn't changed, re-firing the effect every render and
// looping forever ("Maximum update depth exceeded").
export function getNextFightTime(boss) {
  if (boss.fight_window_open && !boss.already_fought_today) return null

  const now = new Date()
  const todayAt17 = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 17, 0, 0)

  if (!boss.fight_window_open) return todayAt17

  // Window is open but already fought — next chance is 17:00 UTC tomorrow.
  return todayAt17 + 24 * 60 * 60 * 1000
}

export function useFightBoss() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: fightBoss,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['boss'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      addToast(
        result.result === 'won'
          ? `Победа! Урон: ${result.damage_dealt}`
          : `Поражение... Урон: ${result.damage_dealt}`,
        result.result === 'won' ? 'success' : 'error'
      )
    },
    onError: () => addToast('Не удалось начать бой', 'error'),
  })
}
