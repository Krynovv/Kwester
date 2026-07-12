import { useMutation, useQueryClient } from '@tanstack/react-query'
import { uploadAvatar } from '../api/user'

export function useUploadAvatar() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: uploadAvatar,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['me'] }),
  })
}
