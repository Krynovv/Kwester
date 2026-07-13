import { useQuery } from '@tanstack/react-query'
import { fetchMe } from '../api/auth'
import StatsOverview from '../components/StatsOverview'
import ActiveQuestsPreview from '../components/ActiveQuestsPreview'
import BossPanel from '../components/BossPanel'

export default function DashboardPage() {
  const { data: user, isLoading } = useQuery({ queryKey: ['me'], queryFn: fetchMe })

  if (isLoading) return <p className="text-gray-300">Загрузка...</p>

  return (
    <div className="space-y-8">
      <h1 className="font-display text-lg text-gray-100">
        ПРИВЕТ, {user?.username?.toUpperCase()}
      </h1>

      <StatsOverview />

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="order-2 lg:order-none lg:col-span-2">
          <ActiveQuestsPreview />
        </div>
        <div className="order-1 lg:order-none">
          <BossPanel />
        </div>
      </div>
    </div>
  )
}
