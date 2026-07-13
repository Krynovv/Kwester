import { Link, NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Heart, Coins, Sword, User } from 'pixelarticons/react'
import { fetchMe } from '../api/auth'

const navItems = [
  { to: '/', label: 'Дашборд' },
  { to: '/quests', label: 'Квесты' },
  { to: '/rewards', label: 'Награды' },
  { to: '/shop', label: 'Магазин' },
]

export default function Layout() {
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: fetchMe })

  return (
    <div className="min-h-screen bg-cyber-bg text-gray-100">
      <header className="flex items-center justify-between gap-2 border-b-2 border-cyber-border bg-cyber-card px-3 py-3 sm:px-6">
        <nav className="flex min-w-0 items-center gap-3 overflow-x-auto sm:gap-5">
          <span className="pixel-hover shrink-0 font-display text-sm text-cyber-primary text-glow">
            <span className="hidden sm:inline">KWESTER</span>
            <span className="sm:hidden">W</span>
          </span>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `shrink-0 whitespace-nowrap font-mono text-sm sm:text-base ${isActive ? 'text-cyber-secondary text-glow' : 'text-gray-400 hover:text-gray-200'}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-2 font-mono text-sm sm:gap-4 sm:text-base">
          <span className="hidden items-center gap-1 text-yellow-400 sm:flex">
            <Coins width={18} height={18} />
            {user?.currency_balance}
          </span>
          <span className="hidden items-center gap-1 text-cyber-secondary sm:flex">
            <Sword width={18} height={18} />
            {user?.boss_currency_balance}
          </span>
          <span className="hidden items-center gap-1 text-cyber-danger sm:flex">
            <Heart width={18} height={18} />
            {user?.current_hp}
          </span>
          <Link
            to="/profile"
            className="pixel-hover flex items-center gap-1 border-2 border-transparent px-2 py-1 text-gray-300 hover:border-cyber-secondary hover:text-cyber-secondary"
          >
            <span className="hidden sm:inline">{user?.username}</span>
            <User width={16} height={16} />
          </Link>
        </div>
      </header>

      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
