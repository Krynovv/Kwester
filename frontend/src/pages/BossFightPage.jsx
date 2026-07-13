import { useEffect } from 'react'
import { Skull, Heart, Clock, Zap, Check, SquareAlert } from 'pixelarticons/react'
import { useBossStatus, useFightBoss, getNextFightTime } from '../hooks/useBoss'
import { useCountdown, formatDuration } from '../hooks/useCountdown'
import Button from '../components/Button'
import BackLink from '../components/BackLink'

export default function BossFightPage() {
  const { data: boss, isLoading, refetch } = useBossStatus()
  const { mutate: fight, isPending } = useFightBoss()

  const nextFightTime = boss ? getNextFightTime(boss) : null
  const remainingMs = useCountdown(nextFightTime)

  useEffect(() => {
    if (nextFightTime && remainingMs === 0) refetch()
  }, [remainingMs, nextFightTime, refetch])

  if (isLoading) return <p className="text-gray-400">Загрузка...</p>
  if (!boss) return null

  const canFight = boss.fight_window_open && !boss.already_fought_today
  const buttonLabel = isPending ? 'Сражаемся...' : canFight ? 'Сразиться' : formatDuration(remainingMs)
  const hpProgress = Math.min(100, (boss.current_hp / boss.max_hp) * 100)
  const damageProgress = Math.min(100, (boss.projected_damage / boss.boss_hp) * 100)

  return (
    <div className="max-w-2xl space-y-8">
      <BackLink to="/" />

      <div className="flex items-center gap-4">
        <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-none border-2 border-cyber-primary bg-cyber-bg pixel-shadow-primary">
          <Skull width={40} height={40} className="text-cyber-primary" />
        </div>
        <div>
          <h1 className="font-display text-base text-gray-100">{boss.boss_name.toUpperCase()}</h1>
          <p className="mt-1 text-base text-gray-400">
            Уровень {boss.boss_level} · HP: {boss.boss_hp}
          </p>
        </div>
      </div>

      <div>
        <p className="mb-1 flex items-center gap-1 text-sm text-gray-400">
          <Heart width={14} height={14} className="text-cyber-danger" />
          Ваше HP: {boss.current_hp}/{boss.max_hp}
        </p>
        <div className="relative h-3 overflow-hidden rounded-none bg-cyber-muted">
          <div
            className="h-full bg-cyber-danger transition-all duration-500 ease-out"
            style={{ width: `${hpProgress}%` }}
          />
          <div className="bar-segments" />
        </div>
      </div>

      <div>
        <p
          className={`mb-1 flex items-center gap-1 text-sm ${boss.is_ready ? 'text-cyber-accent' : 'text-cyber-danger'}`}
        >
          {boss.is_ready ? <Check width={14} height={14} /> : <SquareAlert width={14} height={14} />}
          Урон сегодня: {boss.projected_damage}/{boss.boss_hp} — {boss.is_ready ? 'готовы к бою' : 'не хватит урона'}
        </p>
        <div className="relative h-3 overflow-hidden rounded-none bg-cyber-muted">
          <div
            className={`h-full transition-all duration-500 ease-out ${boss.is_ready ? 'bg-cyber-accent' : 'bg-cyber-danger'}`}
            style={{ width: `${damageProgress}%` }}
          />
          <div className="bar-segments" />
        </div>
      </div>

      <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-4">
        <h2 className="mb-2 flex items-center gap-2 font-display text-xs text-gray-100">
          <Zap width={16} height={16} className="text-cyber-secondary" />
          КАК СЧИТАЕТСЯ УРОН
        </h2>
        <p className="text-base text-gray-400">
          Урон = уровень <span className="text-cyber-primary">Силы</span> × количество{' '}
          <span className="text-cyber-secondary">разных статов</span>, по которым сегодня выполнен хотя бы
          один квест. Не хватит урона — босс ударит в ответ: вы потеряете HP пропорционально недостающему
          урону.
        </p>
      </div>

      <Button variant="primary" onClick={() => fight()} disabled={!canFight || isPending} className="w-full">
        {!canFight && !isPending && <Clock width={16} height={16} className="mr-2 inline align-text-bottom" />}
        {buttonLabel}
      </Button>
    </div>
  )
}
