import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadAvatar } from '../api/user'
import { useToastStore } from '../store/toastStore'

export function useUploadAvatar() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: uploadAvatar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['me'] })
      addToast('Аватарка обновлена', 'success')
    },
    // Ошибка остаётся только в профиле (ProfilePage) — тост был бы дублем.
  })
}
