import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchQuests, createQuest, updateQuest, completeQuest, deleteQuest } from '../api/quests'
import { useToastStore } from '../store/toastStore'

export function useQuests() {
  return useQuery({ queryKey: ['quests'], queryFn: fetchQuests })
}

export function useCreateQuest() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: createQuest,
    onSuccess: (quest) => {
      queryClient.invalidateQueries({ queryKey: ['quests'] })
      addToast(`Квест «${quest.name}» создан`, 'info')
    },
    // Ошибка остаётся только в форме (QuestForm) — там есть поле для fix, тост был бы дублем.
  })
}

export function useUpdateQuest() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: ({ id, data }) => updateQuest(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quests'] })
      addToast('Изменения сохранены', 'info')
    },
    // Ошибка остаётся только в форме редактирования (QuestCard) — тост был бы дублем.
  })
}

export function useCompleteQuest() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: completeQuest,
    onSuccess: (quest) => {
      queryClient.invalidateQueries({ queryKey: ['quests'] })
      queryClient.invalidateQueries({ queryKey: ['me'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
      // Выполнение двигает урон по боссу, а внеплановая привычка ещё и HP.
      queryClient.invalidateQueries({ queryKey: ['boss'] })
      addToast(`«${quest.name}» выполнен: +${quest.reward_xp} XP +${quest.reward_currency} 🪙`, 'success')
    },
    onError: () => addToast('Не удалось выполнить квест', 'error'),
  })
}

export function useDeleteQuest() {
  const queryClient = useQueryClient()
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: deleteQuest,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quests'] })
      addToast('Квест удалён', 'info')
    },
    onError: () => addToast('Не удалось удалить квест', 'error'),
  })
}
