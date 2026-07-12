import { Link } from 'react-router-dom'
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
      <div className="flex items-center justify-between">
        <h2 className="font-display text-lg text-gray-100">АКТИВНЫЕ КВЕСТЫ</h2>
        <Link to="/quests" className="text-sm text-cyber-secondary hover:text-glow">
          Все квесты →
        </Link>
      </div>

      {isLoading ? (
        <p className="mt-2 text-gray-400">Загрузка...</p>
      ) : active.length ? (
        <div className="mt-3 space-y-3">
          {active.map((quest) => (
            <QuestCard key={quest.id} quest={quest} statName={statNameById[quest.stat_id]} />
          ))}
        </div>
      ) : (
        <p className="mt-3 text-gray-500">Нет активных квестов.</p>
      )}
    </div>
  )
}
