import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchShopItems, purchaseShopItem, applyShopItem } from '../api/shop'
import { useToastStore } from '../store/toastStore'

export function useShopItems() {
  return useQuery({ queryKey: ['shop'], queryFn: fetchShopItems })
}

export function usePurchaseShopItem() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: purchaseShopItem,
    onSuccess: (item) => {
      queryClient.invalidateQueries({ queryKey: ['shop'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      queryClient.invalidateQueries({ queryKey: ['boss'] })
      addToast(`Куплено: «${item.name}»`, 'success')
    },
    onError: (error) =>
      addToast(error.response?.data?.detail ?? 'Не удалось купить предмет', 'error'),
  })
}

export function useApplyShopItem() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: applyShopItem,
    onSuccess: (item) => {
      queryClient.invalidateQueries({ queryKey: ['shop'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      queryClient.invalidateQueries({ queryKey: ['boss'] })
      addToast(`Использовано: «${item.name}»`, 'success')
    },
    onError: (error) =>
      addToast(error.response?.data?.detail ?? 'Не удалось использовать предмет', 'error'),
  })
}
