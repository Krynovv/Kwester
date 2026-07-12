import { useParams, Link } from 'react-router-dom'
import { useStats } from '../hooks/useStats'
import { useQuests } from '../hooks/useQuests'
import { statStyle, defaultStatStyle } from '../constants/statStyle'
import QuestCard from '../components/QuestCard'

export default function StatDetailPage() {
  const { statId } = useParams()
  const { data: stats, isLoading: statsLoading } = useStats()
  const { data: quests, isLoading: questsLoading } = useQuests()

  const stat = stats?.find((s) => String(s.id) === statId)
  const linkedQuests = (quests ?? []).filter((q) => String(q.stat_id) === statId)

  if (statsLoading) return <p className="text-gray-400">Загрузка...</p>
  if (!stat) return <p className="text-gray-400">Стат не найден.</p>

  const progress = Math.min(100, (stat.current_xp / stat.xp_to_next_level) * 100)
  const style = statStyle[stat.name] ?? defaultStatStyle
  const Icon = style.icon

  return (
    <div className="max-w-2xl space-y-8">
      <Link to="/" className="text-sm text-cyber-secondary hover:text-glow">
        ← Назад
      </Link>

      <div className="flex items-center">
        <div
          className={`relative z-10 flex h-20 w-20 shrink-0 items-center justify-center rounded-full border-2 bg-cyber-bg ${style.border}`}
        >
          <Icon width={36} height={36} className={style.text} />
        </div>
        <div
          className={`-ml-10 flex h-12 flex-1 items-center rounded-r-full border-2 border-l-0 bg-cyber-muted py-1 pl-14 pr-4 ${style.border}`}
        >
          <div className="relative h-3 w-full overflow-hidden rounded-full bg-cyber-bg">
            <div
              className={`h-full ${style.bar} transition-all duration-500 ease-out`}
              style={{ width: `${progress}%` }}
            />
            <div className="bar-segments" />
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between pl-1 text-sm text-gray-400">
        <span className="font-display text-sm text-gray-100">{stat.name.toUpperCase()}</span>
        <span>
          Ур. <span className={style.text}>{stat.level}</span> · {stat.current_xp} / {stat.xp_to_next_level} XP
        </span>
      </div>

      <div>
        <h2 className="mb-3 font-display text-sm text-gray-100">СВЯЗАННЫЕ КВЕСТЫ</h2>
        {questsLoading ? (
          <p className="text-gray-400">Загрузка...</p>
        ) : linkedQuests.length ? (
          <div className="space-y-3">
            {linkedQuests.map((quest) => (
              <QuestCard key={quest.id} quest={quest} statName={stat.name} />
            ))}
          </div>
        ) : (
          <p className="text-gray-500">
            К этому стату пока не привязано ни одного квеста —{' '}
            <Link to="/quests" className="text-cyber-secondary hover:text-glow">
              создайте один
            </Link>
            .
          </p>
        )}
      </div>
    </div>
  )
}
