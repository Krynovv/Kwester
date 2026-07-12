import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchShopItems, purchaseShopItem } from '../api/shop'

export function useShopItems() {
  return useQuery({ queryKey: ['shop'], queryFn: fetchShopItems })
}

export function usePurchaseShopItem() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: purchaseShopItem,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['shop'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      queryClient.invalidateQueries({ queryKey: ['boss'] })
    },
  })
}
