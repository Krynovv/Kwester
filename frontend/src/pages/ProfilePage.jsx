import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Coins, Sword, Heart, Zap, Logout } from 'pixelarticons/react'
import { fetchMe } from '../api/auth'
import { API_BASE_URL } from '../api/client'
import { useStats } from '../hooks/useStats'
import { useUploadAvatar } from '../hooks/useUser'
import { useAuthStore } from '../store/authStore'
import StatsOverview from '../components/StatsOverview'
import Button from '../components/Button'

export default function ProfilePage() {
  const fileInputRef = useRef(null)
  const logout = useAuthStore((state) => state.logout)
  const { data: user, isLoading } = useQuery({ queryKey: ['me'], queryFn: fetchMe })
  const { data: stats } = useStats()
  const { mutate: upload, isPending: uploading, error: uploadError } = useUploadAvatar()

  const characterLevel = (stats ?? []).reduce((sum, s) => sum + s.level, 0)

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) upload(file)
    e.target.value = ''
  }

  if (isLoading) return <p className="text-gray-400">Загрузка...</p>

  return (
    <div className="max-w-6xl space-y-6">
      <h1 className="font-display text-lg text-gray-100">ПРОФИЛЬ</h1>

      <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-6">
        <div className="flex flex-col items-start gap-6 sm:flex-row">
          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="pixel-hover relative h-36 w-36 overflow-hidden rounded-none border-2 border-cyber-primary bg-cyber-muted pixel-shadow-primary"
              title="Загрузить аватарку"
            >
              {user?.image_file ? (
                <img
                  src={`${API_BASE_URL}/static/images/${user.image_file}`}
                  alt="Аватар"
                  className="h-full w-full object-cover"
                />
              ) : (
                <span className="flex h-full w-full items-center justify-center text-4xl text-gray-400">
                  {user?.username?.[0]?.toUpperCase()}
                </span>
              )}
            </button>
            <span className="absolute -bottom-3 -right-3 flex items-center gap-1 border-2 border-cyber-primary bg-cyber-bg px-2 py-1 text-sm text-cyber-primary text-glow pixel-shadow-primary">
              <Zap width={14} height={14} />
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

            <div className="mt-4 flex flex-wrap gap-5 text-base">
              <span className="flex items-center gap-2 rounded-none border-2 border-cyber-gold bg-cyber-bg px-4 py-2 text-cyber-gold pixel-shadow-gold">
                <Coins width={18} height={18} />
                {user?.currency_balance}
              </span>
              <span className="flex items-center gap-2 rounded-none border-2 border-cyber-secondary bg-cyber-bg px-4 py-2 text-cyber-secondary pixel-shadow-secondary">
                <Sword width={18} height={18} />
                {user?.boss_currency_balance}
              </span>
              <span className="flex items-center gap-2 rounded-none border-2 border-cyber-danger bg-cyber-bg px-4 py-2 text-cyber-danger pixel-shadow-danger">
                <Heart width={18} height={18} />
                {user?.current_hp}
              </span>
              <Button variant="ghost" onClick={logout} className="ml-auto">
                <Logout width={18} height={18} className="mr-2 inline align-text-bottom" />
                Выйти
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-none border-2 border-cyber-border bg-cyber-card p-6">
        <h2 className="mb-3 font-display text-sm text-gray-100">ХАРАКТЕРИСТИКИ</h2>
        <StatsOverview />
      </div>
    </div>
  )
}
