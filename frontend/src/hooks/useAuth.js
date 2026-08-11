import { useMutation } from '@tanstack/react-query'
import { loginUser, registerUser } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import { useToastStore } from '../store/toastStore'

export function useLogin() {
  const setTokens = useAuthStore((state) => state.setTokens)
  const addToast = useToastStore((state) => state.addToast)

  return useMutation({
    mutationFn: ({ username, password }) => loginUser(username, password),
    onSuccess: (data) => {
      setTokens(data.access_token, data.refresh_token)
      addToast('Вход выполнен', 'success')
    },
    // Ошибка остаётся только в форме (LoginPage) — тост был бы дублем.
  })
}

export function useRegister() {
  const addToast = useToastStore((state) => state.addToast)
  return useMutation({
    mutationFn: registerUser,
    onSuccess: () => addToast('Аккаунт создан, теперь войдите', 'success'),
    // Ошибка остаётся только в форме (RegisterPage) — там показывается конкретная причина
    // от backend (например "имя занято"), а не общий тост, который бы её маскировал.
  })
}
