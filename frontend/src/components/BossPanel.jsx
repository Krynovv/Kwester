import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Skull, Heart, Clock, Check, SquareAlert } from 'pixelarticons/react'
import { useBossStatus, useFightBoss, getNextFightTime } from '../hooks/useBoss'
import { useCountdown, formatDuration } from '../hooks/useCountdown'
import Button from './Button'

export default function BossPanel() {
  const navigate = useNavigate()
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
    <div
      role="link"
      tabIndex={0}
      onClick={() => navigate('/boss')}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          navigate('/boss')
        }
      }}
      className="cursor-pointer rounded-none border-2 border-cyber-primary bg-cyber-card p-4 pixel-shadow-primary transition-transform hover:scale-[1.02]"
    >
      <div className="flex items-center gap-2 font-display text-xs text-gray-100">
        <Skull width={20} height={20} className="text-cyber-primary" />
        {boss.boss_name.toUpperCase()} · УР. {boss.boss_level}
      </div>
      <p className="mt-2 text-base text-gray-400">HP босса: {boss.boss_hp}</p>
      <p className="flex items-center gap-1 text-base text-gray-400">
        <Heart width={16} height={16} className="text-cyber-danger" />
        Ваше HP: {boss.current_hp}/{boss.max_hp}
      </p>
      <p
        className={`mt-1 flex items-center gap-1 text-sm ${boss.is_ready ? 'text-cyber-accent' : 'text-cyber-danger'}`}
      >
        {boss.is_ready ? (
          <Check width={14} height={14} />
        ) : (
          <SquareAlert width={14} height={14} />
        )}
        Урон сегодня: {boss.projected_damage}/{boss.boss_hp} {boss.is_ready ? '— готовы' : '— не хватает'}
      </p>

      <Button
        variant="primary"
        onClick={(e) => {
          e.stopPropagation()
          fight()
        }}
        disabled={!canFight || isPending}
        className="mt-3 w-full"
      >
        {!canFight && !isPending && <Clock width={16} height={16} className="mr-2 inline align-text-bottom" />}
        {buttonLabel}
      </Button>
    </div>
  )
}
