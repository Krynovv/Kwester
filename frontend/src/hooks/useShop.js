import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchShopItems, purchaseShopItem } from '../api/shop'
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
    onError: () => addToast('Не удалось купить предмет', 'error'),
  })
}
