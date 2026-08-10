import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Coins, Sword, Heart, Zap, Logout, Package } from 'pixelarticons/react'
import { Link } from 'react-router-dom'
import { fetchMe } from '../api/auth'
import { API_BASE_URL } from '../api/client'
import { useStats } from '../hooks/useStats'
import { useUploadAvatar } from '../hooks/useUser'
import { useShopItems, useApplyShopItem } from '../hooks/useShop'
import { useAuthStore } from '../store/authStore'
import { useLoadoutStore } from '../store/loadoutStore'
import { USABLE_ITEM_KEYS } from '../constants/itemStyle'
import StatsOverview from '../components/StatsOverview'
import Button from '../components/Button'
import InventoryItemCard from '../components/InventoryItemCard'

export default function ProfilePage() {
  const fileInputRef = useRef(null)
  const logout = useAuthStore((state) => state.logout)
  const { data: user, isLoading } = useQuery({ queryKey: ['me'], queryFn: fetchMe })
  const { data: stats } = useStats()
  const { data: shopItems } = useShopItems()
  const { mutate: upload, isPending: uploading, error: uploadError } = useUploadAvatar()
  const armed = useLoadoutStore((state) => state.armed)
  const toggleArm = useLoadoutStore((state) => state.toggle)
  const { mutate: applyItem, isPending: isUsing, variables: usingKey } = useApplyShopItem()

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

            {uploading && <p className="mt-3 text-sm text-gray-400">Загружаем аватарку...</p>}
            {uploadError && (
              <p className="mt-3 text-sm text-cyber-danger">
                Не удалось загрузить изображение (макс. 5MB, jpg/png/webp)
              </p>
            )}
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-3 text-sm sm:flex-row sm:flex-wrap sm:items-center sm:gap-5 sm:text-base">
          <div className="flex items-center gap-2 overflow-x-auto sm:gap-5">
            <span className="flex shrink-0 items-center gap-2 rounded-none border-2 border-cyber-gold bg-cyber-bg px-3 py-1.5 text-cyber-gold pixel-shadow-gold sm:px-4 sm:py-2">
              <Coins width={16} height={16} className="sm:hidden" />
              <Coins width={18} height={18} className="hidden sm:block" />
              {user?.currency_balance}
            </span>
            <span className="flex shrink-0 items-center gap-2 rounded-none border-2 border-cyber-secondary bg-cyber-bg px-3 py-1.5 text-cyber-secondary pixel-shadow-secondary sm:px-4 sm:py-2">
              <Sword width={16} height={16} className="sm:hidden" />
              <Sword width={18} height={18} className="hidden sm:block" />
              {user?.boss_currency_balance}
            </span>
            <span className="flex shrink-0 items-center gap-2 rounded-none border-2 border-cyber-danger bg-cyber-bg px-3 py-1.5 text-cyber-danger pixel-shadow-danger sm:px-4 sm:py-2">
              <Heart width={16} height={16} className="sm:hidden" />
              <Heart width={18} height={18} className="hidden sm:block" />
              {user?.current_hp}
            </span>
          </div>
          <Button variant="ghost" size="sm" onClick={logout} className="w-full sm:ml-auto sm:w-auto">
            <Logout width={16} height={16} className="mr-2 inline align-text-bottom" />
            Выйти
          </Button>
        </div>
      </div>

      <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-4 sm:p-6">
        <h2 className="mb-3 font-display text-sm text-gray-100">ХАРАКТЕРИСТИКИ</h2>
        <StatsOverview />
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
