import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchQuests, createQuest, updateQuest, completeQuest, deleteQuest } from '../api/quests'

export function useQuests() {
  return useQuery({ queryKey: ['quests'], queryFn: fetchQuests })
}

export function useCreateQuest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: createQuest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['quests'] }),
  })
}

export function useUpdateQuest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }) => updateQuest(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['quests'] }),
  })
}

export function useCompleteQuest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: completeQuest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quests'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useDeleteQuest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteQuest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['quests'] }),
  })
}
