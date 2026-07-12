import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchRewards, createReward, updateReward, purchaseReward, deleteReward } from '../api/rewards'
import { useToastStore } from '../store/toastStore'

export function useRewards() {
  return useQuery({ queryKey: ['rewards'], queryFn: fetchRewards })
}

export function useCreateReward() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: createReward,
    onSuccess: (reward) => {
      queryClient.invalidateQueries({ queryKey: ['rewards'] })
      addToast(`Награда «${reward.title}» создана`, 'info')
    },
    // Ошибка остаётся только в форме (RewardForm) — тост был бы дублем.
  })
}

export function useUpdateReward() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: ({ id, data }) => updateReward(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rewards'] })
      addToast('Изменения сохранены', 'info')
    },
    // Ошибка остаётся только в форме редактирования (RewardCard) — тост был бы дублем.
  })
}

export function usePurchaseReward() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: purchaseReward,
    onSuccess: (reward) => {
      queryClient.invalidateQueries({ queryKey: ['rewards'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      addToast(`Куплено: «${reward.title}»`, 'success')
    },
    onError: () => addToast('Не удалось купить награду', 'error'),
  })
}

export function useDeleteReward() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: deleteReward,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rewards'] })
      addToast('Награда удалена', 'info')
    },
    onError: () => addToast('Не удалось удалить награду', 'error'),
  })
}
