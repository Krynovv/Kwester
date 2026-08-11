import { Link } from 'react-router-dom'
import { useStats } from '../hooks/useStats'
import { useLevelUpToasts } from '../hooks/useLevelUpToasts'
import { statStyle, defaultStatStyle } from '../constants/statStyle'

// Внутренняя система координат SVG — размер на экране задаётся снаружи
// через Tailwind (h-12/sm:h-20 и т.п.), viewBox просто масштабирует её.
const VIEW_SIZE = 56
const STROKE = 4
const RADIUS = (VIEW_SIZE - STROKE) / 2
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

// Компактная версия статов для профиля — само кольцо и есть прогресс-бар
// (без отдельной полосы, та уже есть на Главной). Подпись сверху, XP снизу,
// все пять в один ряд; меньше на телефоне, крупнее на десктопе.
export default function StatsRingRow() {
  const { data: stats, isLoading } = useStats()
  const leveledUpIds = useLevelUpToasts(stats)

  if (isLoading) return <p className="text-gray-400">Загрузка статов...</p>

  return (
    <div className="grid grid-cols-5 gap-1 sm:gap-4">
      {stats?.map((stat) => {
        const progress = Math.min(100, (stat.current_xp / stat.xp_to_next_level) * 100)
        const style = statStyle[stat.name] ?? defaultStatStyle
        const Icon = style.icon
        const offset = CIRCUMFERENCE * (1 - progress / 100)

        return (
          <Link
            to={`/stats/${stat.id}`}
            key={stat.id}
            className={`pixel-hover flex flex-col items-center gap-1 ${leveledUpIds.includes(stat.id) ? 'animate-level-up' : ''}`}
          >
            <span className="text-center text-[10px] leading-tight text-gray-500 sm:text-sm">
              {stat.name}
              <br />
              Ур. <span style={{ color: style.accent }}>{stat.level}</span>
            </span>

            <div className="relative h-11 w-11 shrink-0 sm:h-20 sm:w-20">
              <svg viewBox={`0 0 ${VIEW_SIZE} ${VIEW_SIZE}`} className="h-full w-full -rotate-90">
                <circle
                  cx={VIEW_SIZE / 2} cy={VIEW_SIZE / 2} r={RADIUS}
                  fill="none" stroke="var(--color-cyber-muted)" strokeWidth={STROKE}
                />
                <circle
                  cx={VIEW_SIZE / 2} cy={VIEW_SIZE / 2} r={RADIUS}
                  fill="none" stroke={style.accent} strokeWidth={STROKE}
                  strokeDasharray={CIRCUMFERENCE}
                  strokeDashoffset={offset}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dashoffset 500ms ease-out' }}
                />
              </svg>
              <div className="ring-segments" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Icon width={16} height={16} className="sm:hidden" style={{ color: style.accent }} />
                <Icon width={28} height={28} className="hidden sm:block" style={{ color: style.accent }} />
              </div>
            </div>

            <span className="text-center text-[11px] leading-tight text-gray-600 sm:text-base">
              {stat.current_xp}/{stat.xp_to_next_level}
            </span>
          </Link>
        )
      })}
    </div>
  )
}
