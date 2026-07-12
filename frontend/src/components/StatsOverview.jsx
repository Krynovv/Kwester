import { useStats } from '../hooks/useStats'

export default function StatsOverview() {
  const { data: stats, isLoading } = useStats()

  if (isLoading) return <p className="text-gray-400">Загрузка статов...</p>

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
      {stats?.map((stat) => {
        const progress = Math.min(100, (stat.current_xp / stat.xp_to_next_level) * 100)
        return (
          <div key={stat.id} className="rounded-lg border border-cyber-border bg-cyber-card p-3">
            <p className="text-sm text-gray-300">{stat.name}</p>
            <p className="text-xs text-gray-500">Ур. {stat.level}</p>
            <div className="mt-2 h-1.5 rounded-full bg-cyber-muted">
              <div
                className="h-1.5 rounded-full bg-cyber-secondary glow-secondary"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}
