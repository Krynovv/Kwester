import { Link, NavLink, Outlet } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchMe } from '../api/auth'
import { useAuthStore } from '../store/authStore'

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
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="flex items-center justify-between border-b border-gray-800 px-6 py-3">
        <nav className="flex items-center gap-5">
          <span className="font-semibold text-purple-400">Kwester</span>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `text-sm ${isActive ? 'text-white' : 'text-gray-400'}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-4 text-sm">
          <Link to="/profile" className="text-gray-300 hover:text-white">
            {user?.username}
          </Link>
          <span className="text-yellow-400">{user?.currency_balance} 🪙</span>
          <span className="text-orange-400">{user?.boss_currency_balance} ⚔️</span>
          <span className="text-red-400">{user?.current_hp} HP</span>
          <button
            onClick={logout}
            className="rounded bg-gray-800 px-3 py-1 text-gray-200"
          >
            Выйти
          </button>
        </div>
      </header>

      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}
