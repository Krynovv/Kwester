import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchBossStatus, fightBoss } from '../api/boss'
import { useToastStore } from '../store/toastStore'

export function useBossStatus() {
  return useQuery({ queryKey: ['boss'], queryFn: fetchBossStatus })
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
