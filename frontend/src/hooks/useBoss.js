import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchBossStatus, fightBoss } from '../api/boss'
import { useToastStore } from '../store/toastStore'

export function useBossStatus() {
  return useQuery({ queryKey: ['boss'], queryFn: fetchBossStatus })
}

// When can the player fight next? null means "right now".
export function getNextFightTime(boss) {
  if (boss.fight_window_open && !boss.already_fought_today) return null

  const now = new Date()
  const todayAt17 = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 17, 0, 0))

  if (!boss.fight_window_open) return todayAt17

  // Window is open but already fought — next chance is 17:00 UTC tomorrow.
  const tomorrowAt17 = new Date(todayAt17)
  tomorrowAt17.setUTCDate(tomorrowAt17.getUTCDate() + 1)
  return tomorrowAt17
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
