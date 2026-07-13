import { useQuery } from '@tanstack/react-query'
import { Coins } from 'pixelarticons/react'
import { fetchMe } from '../api/auth'
import { useRewards } from '../hooks/useRewards'
import RewardForm from '../components/RewardForm'
import RewardCard from '../components/RewardCard'

export default function RewardsPage() {
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: fetchMe })
  const { data: rewards, isLoading } = useRewards()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-lg text-gray-100">НАГРАДЫ</h1>
        <span className="flex shrink-0 items-center gap-2 rounded-none bg-cyber-bg px-3 py-1.5 text-cyber-gold">
          <Coins width={18} height={18} />
          {user?.currency_balance ?? 0}
        </span>
      </div>

      <RewardForm />

      {isLoading ? (
        <p className="text-gray-400">Загрузка...</p>
      ) : rewards?.length ? (
        <div className="space-y-3">
          {rewards.map((reward) => (
            <RewardCard
              key={reward.id}
              reward={reward}
              currencyBalance={user?.currency_balance ?? 0}
            />
          ))}
        </div>
      ) : (
        <p className="text-gray-500">Наград пока нет — создайте первую выше.</p>
      )}
    </div>
  )
}
