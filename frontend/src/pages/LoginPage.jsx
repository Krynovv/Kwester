import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useLogin } from '../hooks/useAuth'
import Button from '../components/Button'
import PasswordInput from '../components/PasswordInput'

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
    <div className="flex min-h-screen items-center justify-center bg-cyber-bg">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-none border-2 border-cyber-border bg-cyber-card p-8"
      >
        <h1 className="font-display text-base text-cyber-primary text-glow">ВХОД В KWESTER</h1>

        <div className="cyber-input-wrapper">
          <input
            type="text"
            placeholder="Имя пользователя"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="cyber-input w-full rounded-none bg-cyber-muted px-3 py-2 font-sans text-gray-100"
            required
          />
        </div>
        <PasswordInput
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="font-sans"
          required
        />

        {error && (
          <p className="text-sm text-cyber-danger">
            Неверный логин или пароль
          </p>
        )}

        <Button type="submit" variant="primary" disabled={isPending} className="w-full py-2">
          {isPending ? 'Входим...' : 'Войти'}
        </Button>

        <p className="flex items-center justify-between font-sans text-sm text-gray-400">
          Нет аккаунта?
          <Link to="/register" className="text-cyber-secondary hover:text-glow">
            Зарегистрироваться
          </Link>
        </p>
      </form>
    </div>
  )
}
