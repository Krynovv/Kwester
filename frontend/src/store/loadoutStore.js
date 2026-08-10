import { create } from 'zustand'
import { useToastStore } from './toastStore'

// Расходники, выбранные на следующий бой с боссом — армятся тапом по
// карточке в инвентаре (Профиль), расходуются при старте боя
// (service/fight.py::_prepare_consumables). Правило "сумки" здесь
// дублирует бэкенд только для мгновенной обратной связи в UI — финальную
// проверку всё равно делает сервер при старте боя.
export const useLoadoutStore = create((set, get) => ({
  armed: [],

  toggle: (item, { ownsBag, itemsByKey }) => {
    const { armed } = get()
    if (armed.includes(item.key)) {
      set({ armed: armed.filter((key) => key !== item.key) })
      return
    }

    if (armed.length > 0) {
      if (!ownsBag) {
        useToastStore.getState().addToast('Второй расходник требует сумку', 'error')
        return
      }
      if (armed.length >= 2) {
        useToastStore.getState().addToast('Не больше двух расходников за бой', 'error')
        return
      }
      const armedCategories = armed.map((key) => itemsByKey[key]?.category)
      if (armedCategories.includes(item.category)) {
        useToastStore.getState().addToast('Расходники должны быть из разных категорий', 'error')
        return
      }
    }

    set({ armed: [...armed, item.key] })
  },

  clear: () => set({ armed: [] }),
}))
