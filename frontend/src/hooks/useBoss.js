import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchBossStatus, fightBoss } from '../api/boss'

export function useBossStatus() {
  return useQuery({ queryKey: ['boss'], queryFn: fetchBossStatus })
}

export function useFightBoss() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: fightBoss,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['boss'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
