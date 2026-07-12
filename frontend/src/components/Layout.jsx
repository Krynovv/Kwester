import { Link, NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchMe } from '../api/auth'
import { useAuthStore } from '../store/authStore'
import Button from './Button'

const navItems = [
  { to: '/', label: 'Дашборд' },
  { to: '/quests', label: 'Квесты' },
  { to: '/rewards', label: 'Награды' },
  { to: '/shop', label: 'Магазин' },
]

export default function Layout() {
  const logout = useAuthStore((state) => state.logout)
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: fetchMe })

  return (
    <div className="min-h-screen bg-cyber-bg text-gray-100">
      <header className="flex items-center justify-between border-b border-cyber-border bg-cyber-card px-6 py-3">
        <nav className="flex items-center gap-5">
          <span className="glitch-hover font-display text-lg text-cyber-primary text-glow">
            KWESTER
          </span>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `font-mono text-sm ${isActive ? 'text-cyber-secondary text-glow' : 'text-gray-400 hover:text-gray-200'}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-4 font-mono text-sm">
          <Link to="/profile" className="text-gray-300 hover:text-white">
            {user?.username}
          </Link>
          <span className="text-yellow-400">{user?.currency_balance} 🪙</span>
          <span className="text-cyber-secondary">{user?.boss_currency_balance} ⚔️</span>
          <span className="text-cyber-danger">{user?.current_hp} HP</span>
          <Button variant="ghost" size="sm" onClick={logout}>
            Выйти
          </Button>
        </div>
      </header>

      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
