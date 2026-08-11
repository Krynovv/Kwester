import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchBossStatus, fetchActiveFight, fightBoss, takeTurn } from '../api/boss'
import { useToastStore } from '../store/toastStore'
import { useLoadoutStore } from '../store/loadoutStore'

export function useBossStatus() {
  return useQuery({ queryKey: ['boss'], queryFn: fetchBossStatus })
}

// null, пока бой не начат; после старта — активный FightRead с раундами.
export function useActiveFight() {
  return useQuery({ queryKey: ['activeFight'], queryFn: fetchActiveFight })
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

// Старт боя — только создаёт активный FightRead (без result/damage_dealt,
// это ещё не исход). Сами раунды — через useTakeTurn.
export function useFightBoss() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: fightBoss,
    onSuccess: (fight) => {
      queryClient.setQueryData(['activeFight'], fight)
      queryClient.invalidateQueries({ queryKey: ['boss'] })
    },
    onError: (error) =>
      addToast(error.response?.data?.detail ?? 'Не удалось начать бой', 'error'),
  })
}

const FIGHT_END_MESSAGES = {
  won: (fight) => [`Победа! Урон: ${fight.damage_dealt}`, 'success'],
  lost: (fight) => [`Поражение... Урон: ${fight.damage_dealt}`, 'error'],
  timeout: (fight) => [`Раунды кончились. Урон: ${fight.damage_dealt}`, 'info'],
}

export function useTakeTurn() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: takeTurn,
    onSuccess: (fight) => {
      queryClient.setQueryData(['activeFight'], fight)
      if (fight.status !== 'active') {
        queryClient.invalidateQueries({ queryKey: ['me'] })
        queryClient.invalidateQueries({ queryKey: ['stats'] })
        queryClient.invalidateQueries({ queryKey: ['shop'] })
        useLoadoutStore.getState().clear()
        const [message, type] = FIGHT_END_MESSAGES[fight.status](fight)
        addToast(message, type)
      }
    },
    onError: (error) =>
      addToast(error.response?.data?.detail ?? 'Не удалось сделать ход', 'error'),
  })
}
