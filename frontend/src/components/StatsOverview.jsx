import { Link } from 'react-router-dom'
import { useStats } from '../hooks/useStats'
import { useLevelUpToasts } from '../hooks/useLevelUpToasts'
import { statStyle, defaultStatStyle } from '../constants/statStyle'

export default function StatsOverview() {
  const { data: stats, isLoading } = useStats()
  const leveledUpIds = useLevelUpToasts(stats)

  if (isLoading) return <p className="text-gray-400">Загрузка статов...</p>

  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-x-4 gap-y-4">
      {stats?.map((stat) => {
        const progress = Math.min(100, (stat.current_xp / stat.xp_to_next_level) * 100)
        const style = statStyle[stat.name] ?? defaultStatStyle
        const Icon = style.icon
        return (
          <Link
            to={`/stats/${stat.id}`}
            key={stat.id}
            className={`pixel-hover block ${leveledUpIds.includes(stat.id) ? 'animate-level-up' : ''}`}
          >
            <div className="flex items-center">
              {/* Icon badge — a deliberate rounded exception: your own pixel-art icon slot */}
              <div
                className={`relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full border-2 bg-cyber-bg ${style.border}`}
              >
                <Icon width={22} height={22} className={style.text} />
              </div>

              {/* Pill bar, tucked under the badge so they read as one fused shape */}
              <div
                className={`-ml-6 flex h-8 flex-1 items-center rounded-r-full border-2 border-l-0 bg-cyber-muted py-1 pl-8 pr-3 ${style.border}`}
              >
                <div className="relative h-2 w-full overflow-hidden rounded-full bg-cyber-bg">
                  <div
                    className={`h-full ${style.bar} transition-all duration-500 ease-out`}
                    style={{ width: `${progress}%` }}
                  />
                  <div className="bar-segments" />
                </div>
              </div>
            </div>

            <div className="mt-1 flex items-center justify-between pl-1 text-xs text-gray-500">
              <span>
                {stat.name} · Ур. <span className={style.text}>{stat.level}</span>
              </span>
              <span>
                {stat.current_xp} / {stat.xp_to_next_level} XP
              </span>
            </div>
          </Link>
        )
      })}
    </div>
  )
}
