import { useMemo, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Coins, Sword, Heart, Zap, Logout, Package, Clock } from 'pixelarticons/react'
import { Link } from 'react-router-dom'
import { fetchMe, logoutRequest } from '../api/auth'
import { API_BASE_URL } from '../api/client'
import { useStats } from '../hooks/useStats'
import { useUpdateMe, useUploadAvatar } from '../hooks/useUser'
import { useShopItems, useApplyShopItem } from '../hooks/useShop'
import { useAuthStore } from '../store/authStore'
import { useLoadoutStore } from '../store/loadoutStore'
import { USABLE_ITEM_KEYS } from '../constants/itemStyle'
import StatsRingRow from '../components/StatsRingRow'
import Button from '../components/Button'
import InventoryItemCard from '../components/InventoryItemCard'
import Select from '../components/Select'
import {
  FALLBACK_TIMEZONE,
  detectTimezone,
  listTimezones,
  timezoneLabel,
} from '../utils/timezone'

export default function ProfilePage() {
  const fileInputRef = useRef(null)
  const logout = useAuthStore((state) => state.logout)
  const refreshToken = useAuthStore((state) => state.refreshToken)

  const handleLogout = () => {
    if (refreshToken) logoutRequest(refreshToken).catch(() => {})
    logout()
  }
  const { data: user, isLoading } = useQuery({ queryKey: ['me'], queryFn: fetchMe })
  const { data: stats } = useStats()
  const { data: shopItems } = useShopItems()
  const { mutate: upload, isPending: uploading, error: uploadError } = useUploadAvatar()
  const armed = useLoadoutStore((state) => state.armed)
  const toggleArm = useLoadoutStore((state) => state.toggle)
  const { mutate: applyItem, isPending: isUsing, variables: usingKey } = useApplyShopItem()
  const { mutate: updateProfile, isPending: savingProfile } = useUpdateMe()

  const browserTimezone = detectTimezone()
  // Список зон строится из Intl и на несколько сотен пунктов — пересобирать
  // его на каждый ререндер профиля незачем.
  const timezoneOptions = useMemo(() => listTimezones(user?.timezone), [user?.timezone])
  const timezoneMismatch = Boolean(user?.timezone) && user.timezone !== browserTimezone

  const characterLevel = (stats ?? []).reduce((sum, s) => sum + s.level, 0)
  const ownedItems = (shopItems ?? []).filter((item) => item.owned_charges > 0)
  const consumableItems = ownedItems.filter((item) => !item.permanent)
  const permanentItems = ownedItems.filter((item) => item.permanent)
  // Расходники, которые можно взять в бой — не постоянные и с категорией
  // (heal_100/extra_boss_fight применяются вне боя, у них category=null).
  const ownsBag = (shopItems ?? []).some((item) => item.key === 'bag' && item.owned_charges > 0)
  const itemsByKey = Object.fromEntries((shopItems ?? []).map((item) => [item.key, item]))

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) upload(file)
    e.target.value = ''
  }

  if (isLoading) return <p className="text-gray-400">Загрузка...</p>

  return (
    <div className="max-w-6xl space-y-6">
      <h1 className="font-display text-lg text-gray-100">ПРОФИЛЬ</h1>

      <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-4 sm:p-6">
        <div className="flex flex-row items-start gap-4 sm:gap-6">
          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="pixel-hover relative h-20 w-20 overflow-hidden rounded-none border-2 border-cyber-primary bg-cyber-muted pixel-shadow-primary sm:h-36 sm:w-36"
              title="Загрузить аватарку"
            >
              {user?.image_file ? (
                <img
                  src={`${API_BASE_URL}/static/images/${user.image_file}`}
                  alt="Аватар"
                  className="h-full w-full object-cover"
                />
              ) : (
                <span className="flex h-full w-full items-center justify-center text-xl text-gray-400 sm:text-4xl">
                  {user?.username?.[0]?.toUpperCase()}
                </span>
              )}
            </button>
            <span className="absolute -bottom-2 -right-2 flex items-center gap-1 border-2 border-cyber-primary bg-cyber-bg px-1.5 py-0.5 text-xs text-cyber-primary text-glow pixel-shadow-primary sm:-bottom-3 sm:-right-3 sm:px-2 sm:py-1 sm:text-sm">
              <Zap width={12} height={12} />
              LvL {characterLevel}
            </span>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={handleFileChange}
            className="hidden"
          />

          <div className="min-w-0 flex-1 pt-1">
            <p className="text-lg font-medium text-gray-100">{user?.username}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
            <p className="mt-1 font-sans text-sm text-gray-600">
              С нами с {new Date(user?.created_at).toLocaleDateString('ru-RU')}
            </p>

            {/* Десктоп: значения строкой под датой, как и раньше. На мобиле
                узкая колонка рядом с аватаркой не вмещает все три — там
                отдельный полноширинный блок ниже (см. sm:hidden). */}
            <div className="mt-2 hidden items-center gap-5 sm:flex">
              <span className="flex shrink-0 cursor-default items-center gap-2 rounded-none px-4 py-2 text-base text-cyber-gold underline decoration-transparent decoration-2 underline-offset-4 transition-colors hover:decoration-cyber-gold">
                <Coins width={18} height={18} />
                {user?.currency_balance}
              </span>
              <span className="flex shrink-0 cursor-default items-center gap-2 rounded-none px-4 py-2 text-base text-cyber-secondary underline decoration-transparent decoration-2 underline-offset-4 transition-colors hover:decoration-cyber-secondary">
                <Sword width={18} height={18} />
                {user?.boss_currency_balance}
              </span>
              <span className="flex shrink-0 cursor-default items-center gap-2 rounded-none px-4 py-2 text-base text-cyber-danger underline decoration-transparent decoration-2 underline-offset-4 transition-colors hover:decoration-cyber-danger">
                <Heart width={18} height={18} />
                {user?.current_hp}
              </span>
            </div>

            {uploading && <p className="mt-3 text-sm text-gray-400">Загружаем аватарку...</p>}
            {uploadError && (
              <p className="mt-3 text-sm text-cyber-danger">
                Не удалось загрузить изображение (макс. 5MB, jpg/png/webp)
              </p>
            )}
          </div>
        </div>

        {/* Мобиле-only: своя строка на всю ширину карточки под аватаркой —
            там достаточно места для всех трёх значений. */}
        <div className="mt-4 flex flex-wrap items-center gap-2 sm:hidden">
          <span className="flex shrink-0 cursor-default items-center gap-2 rounded-none px-3 py-1.5 text-sm text-cyber-gold underline decoration-transparent decoration-2 underline-offset-4 transition-colors hover:decoration-cyber-gold">
            <Coins width={16} height={16} />
            {user?.currency_balance}
          </span>
          <span className="flex shrink-0 cursor-default items-center gap-2 rounded-none px-3 py-1.5 text-sm text-cyber-secondary underline decoration-transparent decoration-2 underline-offset-4 transition-colors hover:decoration-cyber-secondary">
            <Sword width={16} height={16} />
            {user?.boss_currency_balance}
          </span>
          <span className="flex shrink-0 cursor-default items-center gap-2 rounded-none px-3 py-1.5 text-sm text-cyber-danger underline decoration-transparent decoration-2 underline-offset-4 transition-colors hover:decoration-cyber-danger">
            <Heart width={16} height={16} />
            {user?.current_hp}
          </span>
        </div>

        <div className="mt-4 flex justify-end">
          <Button variant="ghost" size="sm" onClick={handleLogout} className="w-full sm:w-auto">
            <Logout width={16} height={16} className="mr-2 inline align-text-bottom" />
            Выйти
          </Button>
        </div>
      </div>

      <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-4 sm:p-6">
        <h2 className="mb-1 flex items-center gap-2 font-display text-sm text-gray-100">
          <Clock width={18} height={18} className="text-cyber-secondary" />
          ЧАСОВОЙ ПОЯС
        </h2>
        <p className="mb-3 font-sans text-sm text-gray-500">
          По нему считается смена суток: сброс ежедневок, серии привычек и окно боя с боссом.
        </p>

        <Select
          value={user?.timezone ?? FALLBACK_TIMEZONE}
          onChange={(timezone) => updateProfile({ timezone })}
          options={timezoneOptions}
          className="max-w-sm"
        />

        {timezoneMismatch && (
          <div className="mt-3 flex flex-col gap-2 border-2 border-cyber-gold bg-cyber-bg p-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="font-sans text-sm text-cyber-gold">
              Похоже, вы сейчас в {timezoneLabel(browserTimezone)} — сутки считаются не по вашему времени.
            </p>
            <Button
              variant="ghost"
              size="sm"
              disabled={savingProfile}
              onClick={() => updateProfile({ timezone: browserTimezone })}
              className="shrink-0"
            >
              Обновить
            </Button>
          </div>
        )}
      </div>

      <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-4 sm:p-6">
        <h2 className="mb-3 font-display text-sm text-gray-100">ХАРАКТЕРИСТИКИ</h2>
        <StatsRingRow />
      </div>

      <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-4 sm:p-6">
        <h2 className="mb-3 flex items-center gap-2 font-display text-sm text-gray-100">
          <Package width={18} height={18} className="text-cyber-secondary" />
          ИНВЕНТАРЬ
        </h2>
        {ownedItems.length ? (
          <div className="space-y-5">
            {consumableItems.length > 0 && (
              <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 sm:gap-4 lg:grid-cols-6">
                {consumableItems.map((item) => {
                  const armable = !!item.category
                  const usable = USABLE_ITEM_KEYS.has(item.key)
                  return (
                    <InventoryItemCard
                      key={item.key}
                      item={item}
                      armable={armable}
                      armed={armed.includes(item.key)}
                      onToggleArm={armable ? () => toggleArm(item, { ownsBag, itemsByKey }) : undefined}
                      usable={usable}
                      onUse={usable ? () => applyItem(item.key) : undefined}
                      isUsing={usable && isUsing && usingKey === item.key}
                    />
                  )
                })}
              </div>
            )}

            {permanentItems.length > 0 && (
              <div className="border-t-2 border-cyber-border pt-5">
                <h3 className="mb-3 text-xs text-gray-500 uppercase">Постоянные предметы</h3>
                <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 sm:gap-4 lg:grid-cols-6">
                  {permanentItems.map((item) => (
                    <InventoryItemCard key={item.key} item={item} />
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <p className="text-gray-500">
            Пока пусто —{' '}
            <Link to="/shop" className="text-cyber-secondary hover:text-glow">
              загляните в магазин босса
            </Link>
            .
          </p>
        )}
      </div>
    </div>
  )
}
