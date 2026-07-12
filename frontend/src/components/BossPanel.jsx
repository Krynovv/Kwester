import { useBossStatus, useFightBoss } from '../hooks/useBoss'
import Button from './Button'

export default function BossPanel() {
  const { data: boss, isLoading } = useBossStatus()
  const { mutate: fight, isPending } = useFightBoss()

  if (isLoading) return <p className="text-gray-400">Загрузка босса...</p>
  if (!boss) return null

  const canFight = boss.fight_window_open && !boss.already_fought_today

  const buttonLabel = isPending
    ? 'Сражаемся...'
    : boss.already_fought_today
      ? 'Уже сражались сегодня'
      : !boss.fight_window_open
        ? 'Бой откроется в 17:00 UTC'
        : 'Сразиться'

  return (
    <div className="rounded-lg border border-cyber-primary/40 bg-cyber-card p-4">
      <h2 className="font-display text-gray-100">
        {boss.boss_name.toUpperCase()} · УР. {boss.boss_level}
      </h2>
      <p className="mt-1 text-sm text-gray-400">HP босса: {boss.boss_hp}</p>
      <p className="text-sm text-gray-400">
        Ваше HP: {boss.current_hp}/{boss.max_hp}
      </p>

      <Button variant="primary" onClick={() => fight()} disabled={!canFight || isPending} className="mt-3 w-full">
        {buttonLabel}
      </Button>
    </div>
  )
}
