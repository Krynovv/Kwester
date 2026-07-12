import { useMutation } from '@tanstack/react-query'
import { loginUser, registerUser } from '../api/auth'
import { useAuthStore } from '../store/authStore'

export function useLogin() {
  const setToken = useAuthStore((state) => state.setToken)

  return useMutation({
    mutationFn: ({ username, password }) => loginUser(username, password),
    onSuccess: (data) => {
      setToken(data.access_token)
    },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: registerUser,
  })
}
