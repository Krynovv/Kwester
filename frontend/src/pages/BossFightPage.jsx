import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Skull, Heart, Clock, Zap, Check, SquareAlert, Sparkle } from 'pixelarticons/react'
import { useBossStatus, useActiveFight, useFightBoss, getNextFightTime } from '../hooks/useBoss'
import { useCountdown, formatDuration } from '../hooks/useCountdown'
import { useShopItems } from '../hooks/useShop'
import { useLoadoutStore } from '../store/loadoutStore'
import { ACTIONS } from '../constants/battleActions'
import Button from '../components/Button'
import BackLink from '../components/BackLink'
import InventoryItemCard from '../components/InventoryItemCard'

export default function BossFightPage() {
  const navigate = useNavigate()
  const { data: boss, isLoading: bossLoading, refetch } = useBossStatus()
  const { data: activeFight, isLoading: fightLoading } = useActiveFight()
  const { data: shopItems } = useShopItems()
  const { mutate: fight, isPending: isStarting } = useFightBoss()
  const [showHelp, setShowHelp] = useState(false)
  const armed = useLoadoutStore((state) => state.armed)
  const toggleArm = useLoadoutStore((state) => state.toggle)

  // Расходники, которые можно взять в бой — не постоянные, с категорией
  // (heal_100/extra_boss_fight сюда не входят) и реально есть в наличии.
  const armableItems = (shopItems ?? []).filter(
    (item) => !item.permanent && item.category && item.owned_charges > 0
  )
  const ownsBag = (shopItems ?? []).some((item) => item.key === 'bag' && item.owned_charges > 0)
  const itemsByKey = Object.fromEntries((shopItems ?? []).map((item) => [item.key, item]))

  const nextFightTime = boss ? getNextFightTime(boss) : null
  const remainingMs = useCountdown(nextFightTime)

  useEffect(() => {
    if (nextFightTime && remainingMs === 0) refetch()
  }, [remainingMs, nextFightTime, refetch])

  // Бой открывается на отдельной странице-чате — эта страница только
  // готовит бой; как только он реально активен (только что начат или
  // ещё не закончен с прошлого раза), сразу уходим туда.
  useEffect(() => {
    if (activeFight?.status === 'active') navigate('/boss/chat', { replace: true })
  }, [activeFight, navigate])

  if (bossLoading || fightLoading) return <p className="text-gray-400">Загрузка...</p>
  if (!boss) return null
  if (activeFight?.status === 'active') return null

  const canFight = boss.fight_window_open && !boss.already_fought_today
  const buttonLabel = isStarting ? 'Начинаем...' : canFight ? 'Сразиться' : formatDuration(remainingMs)
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
        <div className="flex items-center justify-between gap-2">
          <h2 className="flex items-center gap-2 font-display text-xs text-gray-100">
            <Zap width={16} height={16} className="text-cyber-secondary" />
            КАК ИДЁТ БОЙ
          </h2>
          <button
            type="button"
            onClick={() => setShowHelp((v) => !v)}
            aria-expanded={showHelp}
            aria-label={showHelp ? 'Скрыть объяснение' : 'Показать объяснение'}
            className="flex h-7 w-7 shrink-0 items-center justify-center border-2 border-cyber-secondary text-cyber-secondary transition-transform hover:scale-110 active:scale-90"
          >
            <SquareAlert width={16} height={16} />
          </button>
        </div>
        {showHelp && (
          <>
            <p className="mt-3 text-base text-gray-400">
              До 7 раундов, вы ходите первым: на каждый раунд выбираете{' '}
              <span className="text-cyber-primary">Атаку</span>,{' '}
              <span className="text-cyber-secondary">Шутку</span> или{' '}
              <span className="text-cyber-accent">Отговорку</span>, затем отвечает босс. Победа — если собьёте
              ему HP до нуля; если раунды кончились и оба живы — исход решает, у кого HP осталось больше в
              процентах.
            </p>
            <div className="mt-3 space-y-2 border-t-2 border-cyber-border pt-3">
              {ACTIONS.map(({ value, label, hint, icon: Icon, accent }) => (
                <p key={value} className="flex items-start gap-2 text-sm text-gray-400">
                  <Icon width={16} height={16} className="mt-0.5 shrink-0" style={{ color: accent }} />
                  <span>
                    <span className="font-display text-[10px]" style={{ color: accent }}>{label}</span>
                    {' — '}{hint}
                  </span>
                </p>
              ))}
            </div>
          </>
        )}
      </div>

      {armableItems.length > 0 && (
        <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-4">
          <h2 className="mb-2 flex items-center gap-2 font-display text-xs text-gray-100">
            <Sparkle width={16} height={16} className="text-cyber-secondary" />
            ВЗЯТЬ В БОЙ
          </h2>
          <p className="mb-3 text-sm text-gray-500">
            {ownsBag
              ? 'Можно выбрать до двух расходников из разных категорий.'
              : 'Можно выбрать один расходник (сумка из магазина откроет второй слот).'}
          </p>
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-6">
            {armableItems.map((item) => (
              <InventoryItemCard
                key={item.key}
                item={item}
                armable
                armed={armed.includes(item.key)}
                onToggleArm={() => toggleArm(item, { ownsBag, itemsByKey })}
              />
            ))}
          </div>
        </div>
      )}

      <Button
        variant="primary"
        onClick={() => fight(armed)}
        disabled={!canFight || isStarting}
        className="w-full"
      >
        {!canFight && !isStarting && <Clock width={16} height={16} className="mr-2 inline align-text-bottom" />}
        {buttonLabel}
      </Button>
    </div>
  )
}
