import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchRewards, createReward, updateReward, purchaseReward, deleteReward } from '../api/rewards'

export function useRewards() {
  return useQuery({ queryKey: ['rewards'], queryFn: fetchRewards })
}

export function useCreateReward() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createReward,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rewards'] }),
  })
}

export function useUpdateReward() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => updateReward(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rewards'] }),
  })
}

export function usePurchaseReward() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: purchaseReward,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rewards'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
    },
  })
}

export function useDeleteReward() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteReward,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rewards'] }),
  })
}
