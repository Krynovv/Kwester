import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useRegister } from '../hooks/useAuth'
import Button from '../components/Button'

export default function RegisterPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()
  const { mutate, isPending, error } = useRegister()

  const handleSubmit = (e) => {
    e.preventDefault()
    mutate(
      { username, email, password },
      { onSuccess: () => navigate('/login') }
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-cyber-bg">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg border border-cyber-border bg-cyber-card p-8"
      >
        <h1 className="font-display text-xl text-cyber-primary text-glow">РЕГИСТРАЦИЯ</h1>

        <input
          type="text"
          placeholder="Имя пользователя"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-gray-100"
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-gray-100"
          required
        />
        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded border border-cyber-border bg-cyber-muted px-3 py-2 text-gray-100"
          required
        />

        {error && (
          <p className="text-sm text-cyber-danger">
            {error.response?.data?.detail ?? 'Не удалось зарегистрироваться'}
          </p>
        )}

        <Button type="submit" variant="primary" disabled={isPending} className="w-full py-2">
          {isPending ? 'Создаём аккаунт...' : 'Зарегистрироваться'}
        </Button>

        <p className="text-sm text-gray-400">
          Уже есть аккаунт?{' '}
          <Link to="/login" className="text-cyber-secondary hover:text-glow">
            Войти
          </Link>
        </p>
      </form>
    </div>
  )
}
