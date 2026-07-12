import { Link, NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Heart, Coins, Sword, Logout, User } from 'pixelarticons/react'
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
      <header className="flex items-center justify-between border-b-2 border-cyber-border bg-cyber-card px-6 py-3">
        <nav className="flex items-center gap-5">
          <span className="pixel-hover font-display text-sm text-cyber-primary text-glow">
            KWESTER
          </span>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `font-mono text-base ${isActive ? 'text-cyber-secondary text-glow' : 'text-gray-400 hover:text-gray-200'}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-4 font-mono text-base">
          <Link
            to="/profile"
            className="pixel-hover flex items-center gap-1 border-2 border-transparent px-2 py-1 text-gray-300 hover:border-cyber-secondary hover:text-cyber-secondary"
          >
            <User width={16} height={16} />
            {user?.username}
          </Link>
          <span className="flex items-center gap-1 text-yellow-400">
            <Coins width={18} height={18} />
            {user?.currency_balance}
          </span>
          <span className="flex items-center gap-1 text-cyber-secondary">
            <Sword width={18} height={18} />
            {user?.boss_currency_balance}
          </span>
          <span className="flex items-center gap-1 text-cyber-danger">
            <Heart width={18} height={18} />
            {user?.current_hp}
          </span>
          <Button variant="ghost" size="sm" onClick={logout} aria-label="Выйти" title="Выйти">
            <Logout width={18} height={18} />
          </Button>
        </div>
      </header>

      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
