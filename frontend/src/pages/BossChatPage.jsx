import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Skull, Sword, Sparkle } from 'pixelarticons/react'
import { fetchMe } from '../api/auth'
import { API_BASE_URL } from '../api/client'
import { useBossStatus, useActiveFight, useTakeTurn } from '../hooks/useBoss'
import { useShopItems } from '../hooks/useShop'
import { ITEM_ICONS, accentFor } from '../constants/itemStyle'
import { ACTIONS } from '../constants/battleActions'
import Button from '../components/Button'
import BackLink from '../components/BackLink'

const FIGHT_END_LABELS = {
  won: { text: 'ПОБЕДА', className: 'text-cyber-accent' },
  lost: { text: 'ПОРАЖЕНИЕ', className: 'text-cyber-danger' },
  timeout: { text: 'РАУНДЫ КОНЧИЛИСЬ', className: 'text-cyber-gold' },
}

// Показывает "−N" на секунду поверх HP, когда значение падает — не при
// любом изменении (реген не должен мигать тем же индикатором).
function useFloatingDamage(value) {
  const prevRef = useRef(value)
  const [delta, setDelta] = useState(null)

  useEffect(() => {
    const prev = prevRef.current
    if (prev != null && value < prev) {
      setDelta(prev - value)
      const timer = setTimeout(() => setDelta(null), 1100)
      prevRef.current = value
      return () => clearTimeout(timer)
    }
    prevRef.current = value
  }, [value])

  return delta
}

// Карточка бойца в шапке — босс слева, игрок справа зеркально (аватар,
// имя, HP-полоса развёрнуты в противоположную сторону).
function FighterCard({ mirrored, avatar, avatarBorderClass, name, current, max, barClass, floatingDelta }) {
  const progress = max > 0 ? Math.min(100, (current / max) * 100) : 0
  return (
    <div className={`flex items-center gap-3 ${mirrored ? 'flex-row-reverse text-right' : ''}`}>
      <div
        className={`relative flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden border-2 bg-cyber-bg ${avatarBorderClass}`}
      >
        {avatar}
        {floatingDelta != null && (
          <span className="animate-float-damage pointer-events-none absolute -top-2 left-1/2 -translate-x-1/2 font-display text-xs text-cyber-danger">
            −{floatingDelta}
          </span>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate font-display text-[11px] text-gray-100">{name}</p>
        <p className="mt-1 text-xs text-gray-500">{current}/{max}</p>
        <div className="relative mt-1 h-2 overflow-hidden rounded-none bg-cyber-muted">
          <div className={`h-full transition-all duration-500 ease-out ${barClass}`} style={{ width: `${progress}%` }} />
        </div>
      </div>
    </div>
  )
}

// Реплика в боевом чате: свои действия — справа, ответы босса — слева,
// как в обычном мессенджере (см. artifacts/figma boss_chat.pdf).
function ChatBubble({ entry }) {
  const isPlayer = entry.actor === 'player'
  const action = isPlayer ? ACTIONS.find((a) => a.value === entry.action) : null
  const Icon = isPlayer ? (action?.icon ?? Sword) : Skull
  const accent = isPlayer ? (action?.accent ?? 'var(--color-cyber-primary)') : 'var(--color-cyber-danger)'
  const text = isPlayer ? (action?.label ?? entry.action) : 'Атакует'
  const outcome = entry.hit ? (entry.crit ? `КРИТ −${entry.damage}` : `−${entry.damage}`) : 'мимо'

  return (
    <div className={`flex items-end gap-2 ${isPlayer ? 'flex-row-reverse' : ''}`}>
      <span
        className="flex h-7 w-7 shrink-0 items-center justify-center border-2"
        style={{ borderColor: accent, color: accent }}
      >
        <Icon width={14} height={14} />
      </span>
      <div
        className={`max-w-[75%] border-2 bg-cyber-bg px-3 py-1.5 ${isPlayer ? 'text-right' : 'text-left'}`}
        style={{ borderColor: accent }}
      >
        <p className="text-sm text-gray-200">{text}</p>
        <p className={`text-sm ${entry.hit ? (entry.crit ? 'text-cyber-gold' : 'text-gray-500') : 'text-gray-600'}`}>
          {outcome}
        </p>
      </div>
    </div>
  )
}

// Слот расходника у панели действий — max 2 предмета на бой (правило
// "сумки", см. service/fight.py::_prepare_consumables), поэтому слотов
// ровно два: пустой — не значит "нельзя", значит "не взяли".
function ConsumableSlot({ item }) {
  if (!item) {
    return (
      <div className="flex h-12 w-12 shrink-0 items-center justify-center border-2 border-dashed border-cyber-border text-gray-700">
        <span className="text-lg leading-none">·</span>
      </div>
    )
  }
  const Icon = ITEM_ICONS[item.key] ?? Sparkle
  const accent = accentFor(item)
  return (
    <div
      title={item.name}
      className="flex h-12 w-12 shrink-0 items-center justify-center border-2 bg-cyber-bg"
      style={{ borderColor: accent, color: accent }}
    >
      <Icon width={20} height={20} />
    </div>
  )
}

function StunNote() {
  return (
    <p className="text-center text-sm text-gray-500">
      Босс потерял дар речи от шутки и пропускает ход
    </p>
  )
}

function TypingBubble() {
  return (
    <div className="flex items-end gap-2">
      <span className="flex h-7 w-7 shrink-0 items-center justify-center border-2 border-cyber-danger text-cyber-danger">
        <Skull width={14} height={14} />
      </span>
      <div className="border-2 border-cyber-danger bg-cyber-bg px-3 py-2">
        <p className="flex items-center gap-1 text-sm text-gray-500">
          Босс думает
          <span className="typing-dot" style={{ animationDelay: '0ms' }}>.</span>
          <span className="typing-dot" style={{ animationDelay: '150ms' }}>.</span>
          <span className="typing-dot" style={{ animationDelay: '300ms' }}>.</span>
        </p>
      </div>
    </div>
  )
}

export default function BossChatPage() {
  const navigate = useNavigate()
  const { data: boss, isLoading: bossLoading } = useBossStatus()
  const { data: fight, isLoading: fightLoading } = useActiveFight()
  const { data: user } = useQuery({ queryKey: ['me'], queryFn: fetchMe })
  const { data: shopItems } = useShopItems()
  const { mutate: turn, isPending: isTurning } = useTakeTurn()
  const queryClient = useQueryClient()

  const bossDamage = useFloatingDamage(fight?.boss_hp)
  const playerDamage = useFloatingDamage(fight?.player_hp)
  const [pendingAction, setPendingAction] = useState(null)
  const feedEndRef = useRef(null)

  // Открыли /boss/chat напрямую без активного боя (или бой уже "вернули")
  // — тут делать нечего, назад на инфо-экран.
  useEffect(() => {
    if (!fightLoading && !fight) navigate('/boss', { replace: true })
  }, [fightLoading, fight, navigate])

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ block: 'end' })
  }, [fight?.rounds.length, pendingAction])

  if (bossLoading || fightLoading || !fight || !boss) {
    return <p className="text-gray-400">Загрузка...</p>
  }

  const finished = fight.status !== 'active'
  const endLabel = FIGHT_END_LABELS[fight.status]
  const armedItems = fight.active_consumables
    .map((key) => shopItems?.find((item) => item.key === key))
    .filter(Boolean)

  const handleAction = (action) => {
    setPendingAction(action)
    turn(action, { onSettled: () => setPendingAction(null) })
  }

  const handleReturn = () => {
    queryClient.invalidateQueries({ queryKey: ['activeFight'] })
    queryClient.invalidateQueries({ queryKey: ['boss'] })
    navigate('/boss')
  }

  const pendingActionMeta = pendingAction ? ACTIONS.find((a) => a.value === pendingAction) : null

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <BackLink to="/boss" />

      <div className="grid grid-cols-2 items-start gap-4">
        <FighterCard
          avatar={<Skull width={30} height={30} className="text-cyber-primary" />}
          avatarBorderClass="border-cyber-primary"
          name={boss.boss_name.toUpperCase()}
          current={fight.boss_hp}
          max={fight.boss_max_hp}
          barClass="bg-cyber-primary"
          floatingDelta={bossDamage}
        />
        <FighterCard
          mirrored
          avatar={
            user?.image_file ? (
              <img
                src={`${API_BASE_URL}/static/images/${user.image_file}`}
                alt=""
                className="h-full w-full object-cover"
              />
            ) : (
              <span className="font-display text-sm text-cyber-secondary">
                {user?.username?.[0]?.toUpperCase() ?? '?'}
              </span>
            )
          }
          avatarBorderClass="border-cyber-secondary"
          name={user?.username ?? 'Вы'}
          current={fight.player_hp}
          max={fight.player_max_hp}
          barClass="bg-cyber-danger"
          floatingDelta={playerDamage}
        />
      </div>

      <p className="text-center text-sm text-gray-500">Раунд {fight.current_round}</p>

      {/* calc, не vh: ниже ленты — закреплённая внизу вьюпорта панель
          действий (~120px), а над ней — шапка бойцов переменной высоты;
          без вычета лента могла бы визуально уехать под панель. */}
      <div className="h-[calc(100vh-380px)] min-h-32 space-y-3 overflow-y-auto border-2 border-cyber-border bg-cyber-card p-3">
        {fight.rounds.length === 0 && !pendingAction && (
          <p className="py-6 text-center text-sm text-gray-500">Выберите действие — бой начнётся с вашего хода.</p>
        )}
        {fight.rounds.map((entry, i) => {
          const prev = fight.rounds[i - 1]
          // Крит "шуткой" затыкает босса — за раундом игрока сразу следующий
          // раунд, без ответа босса. Отмечаем это отдельной строкой.
          const stunnedBossThisRound =
            prev?.actor === 'player' && prev.action === 'joke' && prev.crit &&
            entry.round_no !== prev.round_no
          return (
            <div key={i}>
              {stunnedBossThisRound && <StunNote />}
              <ChatBubble entry={entry} />
            </div>
          )
        })}
        {pendingAction && (
          <div className="flex flex-row-reverse items-end gap-2 opacity-60">
            <span
              className="flex h-7 w-7 shrink-0 items-center justify-center border-2"
              style={{ borderColor: pendingActionMeta.accent, color: pendingActionMeta.accent }}
            >
              <pendingActionMeta.icon width={14} height={14} />
            </span>
            <div className="max-w-[75%] border-2 bg-cyber-bg px-3 py-1.5 text-right" style={{ borderColor: pendingActionMeta.accent }}>
              <p className="text-sm text-gray-200">{pendingActionMeta.label}</p>
            </div>
          </div>
        )}
        {isTurning && <TypingBubble />}
        <div ref={feedEndRef} />
      </div>

      {finished && (
        <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-4 text-center">
          <p className={`font-display text-sm ${endLabel.className}`}>{endLabel.text}</p>
          <p className="mt-2 text-sm text-gray-400">Урон боссу за бой: {fight.damage_dealt}</p>
          <Button variant="ghost" size="sm" onClick={handleReturn} className="mt-3">
            Вернуться
          </Button>
        </div>
      )}

      {/* Резерв места под закреплённую панель, чтобы конец ленты/баннер
          исхода не прятались под ней. */}
      {!finished && <div className="h-28" aria-hidden="true" />}

      {!finished && (
        // Панель действий закреплена внизу вьюпорта — иконка "выпрыгивает"
        // и увеличивается при наведении/нажатии, сама панель слегка
        // реагирует целиком — см. https://uiverse.io/Mayurwaghgpr/foolish-liger-76
        // (адаптировано под пиксельный стиль игры: без скруглений, с hard
        // pixel-shadow).
        <div className="fixed inset-x-0 bottom-4 z-20 flex items-center justify-center gap-3 px-4">
          <ConsumableSlot item={armedItems[0]} />
          <div className="flex w-fit items-end gap-5 border-2 border-cyber-border bg-cyber-card px-5 py-3 pixel-shadow-ghost transition-transform duration-300 hover:scale-[1.03]">
            {ACTIONS.map(({ value, label, hint, icon: Icon, accent }) => (
              <button
                key={value}
                type="button"
                onClick={() => handleAction(value)}
                disabled={isTurning}
                title={hint}
                className="flex flex-col items-center gap-1.5 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <span
                  className="flex h-12 w-12 items-center justify-center border-2 bg-cyber-bg transition-all duration-300 hover:-translate-y-2 hover:scale-110 active:translate-y-0 active:scale-90"
                  style={{ borderColor: accent, color: accent }}
                >
                  <Icon width={22} height={22} />
                </span>
                <span className="text-xs text-gray-400">{label}</span>
              </button>
            ))}
          </div>
          <ConsumableSlot item={armedItems[1]} />
        </div>
      )}
    </div>
  )
}
