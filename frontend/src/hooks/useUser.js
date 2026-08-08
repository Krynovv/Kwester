import { useMutation, useQueryClient } from '@tanstack/react-query'
import { updateMe, uploadAvatar } from '../api/user'
import { useToastStore } from '../store/toastStore'

export function useUpdateMe() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: updateMe,
    onSuccess: () => {
      // Пояс сдвигает границу суток, поэтому вместе с профилем устаревают
      // квесты (сброс ежедневок) и статус босса (окно боя).
      queryClient.invalidateQueries({ queryKey: ['me'] })
      queryClient.invalidateQueries({ queryKey: ['quests'] })
      queryClient.invalidateQueries({ queryKey: ['boss'] })
      addToast('Профиль обновлён', 'success')
    },
    onError: () => addToast('Не удалось обновить профиль', 'error'),
  })
}

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
