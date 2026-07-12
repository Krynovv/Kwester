import { useState } from 'react'
import { useBossStatus, useFightBoss } from '../hooks/useBoss'

export default function BossPanel() {
  const { data: boss, isLoading } = useBossStatus()
  const { mutate: fight, isPending, error } = useFightBoss()
  const [result, setResult] = useState(null)

  if (isLoading) return <p className="text-gray-400">Загрузка босса...</p>
  if (!boss) return null

  const canFight = boss.fight_window_open && !boss.already_fought_today

  const handleFight = () => {
    fight(undefined, { onSuccess: (data) => setResult(data) })
  }

  const buttonLabel = isPending
    ? 'Сражаемся...'
    : boss.already_fought_today
      ? 'Уже сражались сегодня'
      : !boss.fight_window_open
        ? 'Бой откроется в 17:00 UTC'
        : 'Сразиться'

  return (
    <div className="rounded-lg border border-red-900 bg-gray-900 p-4">
      <h2 className="font-medium text-gray-100">
        {boss.boss_name} · ур. {boss.boss_level}
      </h2>
      <p className="mt-1 text-sm text-gray-400">HP босса: {boss.boss_hp}</p>
      <p className="text-sm text-gray-400">
        Ваше HP: {boss.current_hp}/{boss.max_hp}
      </p>

      <button
        onClick={handleFight}
        disabled={!canFight || isPending}
        className="mt-3 w-full rounded bg-red-700 py-2 text-sm font-medium text-white disabled:opacity-40"
      >
        {buttonLabel}
      </button>

      {error && <p className="mt-2 text-sm text-red-400">Не удалось начать бой</p>}

      {result && (
        <p
          className={`mt-2 text-sm ${result.result === 'won' ? 'text-green-400' : 'text-red-400'}`}
        >
          {result.result === 'won' ? 'Победа!' : 'Поражение...'} Урон: {result.damage_dealt}
        </p>
      )}
    </div>
  )
}
