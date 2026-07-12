import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Skull, Heart, Clock } from 'pixelarticons/react'
import { useBossStatus, useFightBoss, getNextFightTime } from '../hooks/useBoss'
import { useCountdown, formatDuration } from '../hooks/useCountdown'
import Button from './Button'

export default function BossPanel() {
  const { data: boss, isLoading, refetch } = useBossStatus()
  const { mutate: fight, isPending } = useFightBoss()

  const nextFightTime = boss ? getNextFightTime(boss) : null
  const remainingMs = useCountdown(nextFightTime)

  // The countdown hitting zero doesn't itself know the fight window opened —
  // re-check with the server once it does, so the button unlocks on its own.
  useEffect(() => {
    if (nextFightTime && remainingMs === 0) refetch()
  }, [remainingMs, nextFightTime, refetch])

  if (isLoading) return <p className="text-gray-400">Загрузка босса...</p>
  if (!boss) return null

  const canFight = boss.fight_window_open && !boss.already_fought_today

  const buttonLabel = isPending ? 'Сражаемся...' : canFight ? 'Сразиться' : formatDuration(remainingMs)

  return (
    <div className="rounded-none border-2 border-cyber-primary bg-cyber-card p-4 pixel-shadow-primary">
      <Link to="/boss" className="pixel-hover flex items-center gap-2 font-display text-xs text-gray-100">
        <Skull width={20} height={20} className="text-cyber-primary" />
        {boss.boss_name.toUpperCase()} · УР. {boss.boss_level}
      </Link>
      <p className="mt-2 text-base text-gray-400">HP босса: {boss.boss_hp}</p>
      <p className="flex items-center gap-1 text-base text-gray-400">
        <Heart width={16} height={16} className="text-cyber-danger" />
        Ваше HP: {boss.current_hp}/{boss.max_hp}
      </p>

      <Button variant="primary" onClick={() => fight()} disabled={!canFight || isPending} className="mt-3 w-full">
        {!canFight && !isPending && <Clock width={16} height={16} className="mr-2 inline align-text-bottom" />}
        {buttonLabel}
      </Button>
    </div>
  )
}
