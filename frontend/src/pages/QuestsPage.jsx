import { useQuests } from '../hooks/useQuests'
import { useStats } from '../hooks/useStats'
import QuestForm from '../components/QuestForm'
import QuestCard from '../components/QuestCard'

export default function QuestsPage() {
  const { data: quests, isLoading } = useQuests()
  const { data: stats } = useStats()

  const statNameById = Object.fromEntries((stats ?? []).map((s) => [s.id, s.name]))

  return (
    <div className="space-y-6">
      <h1 className="font-display text-lg text-gray-100">КВЕСТЫ</h1>

      <QuestForm />

      {isLoading ? (
        <p className="text-gray-400">Загрузка...</p>
      ) : quests?.length ? (
        <div className="space-y-3">
          {quests.map((quest) => (
            <QuestCard
              key={quest.id}
              quest={quest}
              statName={statNameById[quest.stat_id]}
              statName2={statNameById[quest.stat_id_2]}
            />
          ))}
        </div>
      ) : (
        <p className="text-gray-500">Квестов пока нет — создайте первый выше.</p>
      )}
    </div>
  )
}
