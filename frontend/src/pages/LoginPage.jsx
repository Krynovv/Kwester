import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useLogin } from '../hooks/useAuth'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const { mutate, isPending, error } = useLogin()

  const handleSubmit = (e) => {
    e.preventDefault()
    mutate(
      { username, password },
      { onSuccess: () => navigate('/') }
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-gray-800 bg-gray-900 p-8"
      >
        <h1 className="text-xl font-semibold text-gray-100">Вход в Kwester</h1>

        <input
          type="text"
          placeholder="Имя пользователя"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100"
          required
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded border border-gray-700 bg-gray-800 px-3 py-2 text-gray-100"
          required
        />

        {error && (
          <p className="text-sm text-red-400">
            Неверный логин или пароль
          </p>
        )}

        <button
          type="submit"
          disabled={isPending}
          className="w-full rounded bg-purple-600 py-2 font-medium text-white disabled:opacity-50"
        >
          {isPending ? 'Входим...' : 'Войти'}
        </button>

        <p className="text-sm text-gray-400">
          Нет аккаунта?{' '}
          <Link to="/register" className="text-purple-400">
            Зарегистрироваться
          </Link>
        </p>
      </form>
    </div>
  )
}
