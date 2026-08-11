import { Link } from 'react-router-dom'
import { ArrowRight } from 'pixelarticons/react'
import { useQuests } from '../hooks/useQuests'
import { useStats } from '../hooks/useStats'
import QuestCard from './QuestCard'

export default function ActiveQuestsPreview() {
  const { data: quests, isLoading } = useQuests()
  const { data: stats } = useStats()

  const statNameById = Object.fromEntries((stats ?? []).map((s) => [s.id, s.name]))
  const active = (quests ?? []).filter((q) => q.status === 'active').slice(0, 3)

  return (
    <div>
      <div className="flex flex-col items-start gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="font-display text-lg text-gray-100">АКТИВНЫЕ КВЕСТЫ</h2>
        <Link
          to="/quests"
          className="flex shrink-0 items-center gap-1 whitespace-nowrap text-sm text-cyber-secondary hover:text-glow"
        >
          Все квесты
          <ArrowRight width={14} height={14} />
        </Link>
      </div>

      {isLoading ? (
        <p className="mt-2 text-gray-400">Загрузка...</p>
      ) : active.length ? (
        <div className="mt-3 space-y-3">
          {active.map((quest) => (
            <QuestCard
              key={quest.id}
              quest={quest}
              statName={statNameById[quest.stat_id]}
              statName2={statNameById[quest.stat_id_2]}
            />
          ))}
        </div>
      ) : (
        <p className="mt-3 text-gray-500">Нет активных квестов.</p>
      )}
    </div>
  )
}
