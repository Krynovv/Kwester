import { useQuery } from '@tanstack/react-query'
import { fetchMe } from '../api/auth'

export default function DashboardPage() {
  const { data: user, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: fetchMe,
  })

  if (isLoading) return <p className="text-gray-300">Загрузка...</p>

  return (
    <div>
      <h1 className="text-2xl font-semibold">Привет, {user?.username}!</h1>
      <p className="mt-2 text-gray-400">Баланс валюты: {user?.currency_balance}</p>
    </div>
  )
}
