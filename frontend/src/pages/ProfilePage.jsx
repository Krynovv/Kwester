import { useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Coins, Sword, Heart } from 'pixelarticons/react'
import { fetchMe } from '../api/auth'
import { API_BASE_URL } from '../api/client'
import { useStats } from '../hooks/useStats'
import { useUploadAvatar } from '../hooks/useUser'
import StatsOverview from '../components/StatsOverview'

export default function ProfilePage() {
  const fileInputRef = useRef(null)
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
    <div className="max-w-2xl space-y-8">
      <h1 className="font-display text-lg text-gray-100">ПРОФИЛЬ</h1>

      <div className="flex items-center gap-5">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="pixel-hover relative h-20 w-20 shrink-0 overflow-hidden rounded-none border-2 border-cyber-primary bg-cyber-muted pixel-shadow-primary"
          title="Загрузить аватарку"
        >
          {user?.image_file ? (
            <img
              src={`${API_BASE_URL}/static/images/${user.image_file}`}
              alt="Аватар"
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="flex h-full w-full items-center justify-center text-2xl text-gray-400">
              {user?.username?.[0]?.toUpperCase()}
            </span>
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          onChange={handleFileChange}
          className="hidden"
        />

        <div>
          <p className="text-lg font-medium text-gray-100">{user?.username}</p>
          <p className="text-sm text-gray-500">{user?.email}</p>
          <p className="mt-1 text-sm text-gray-600">
            С нами с {new Date(user?.created_at).toLocaleDateString('ru-RU')}
          </p>
        </div>
      </div>

      {uploading && <p className="text-sm text-gray-400">Загружаем аватарку...</p>}
      {uploadError && (
        <p className="text-sm text-cyber-danger">Не удалось загрузить изображение (макс. 5MB, jpg/png/webp)</p>
      )}

      <div className="flex flex-wrap gap-4 text-base">
        <span className="rounded-none border-2 border-cyber-border bg-cyber-card px-4 py-2 text-gray-300">
          Уровень персонажа: <span className="text-cyber-secondary text-glow">{characterLevel}</span>
        </span>
        <span className="flex items-center gap-2 rounded-none border-2 border-cyber-border bg-cyber-card px-4 py-2 text-yellow-500">
          <Coins width={18} height={18} />
          {user?.currency_balance}
        </span>
        <span className="flex items-center gap-2 rounded-none border-2 border-cyber-border bg-cyber-card px-4 py-2 text-cyber-secondary">
          <Sword width={18} height={18} />
          {user?.boss_currency_balance}
        </span>
        <span className="flex items-center gap-2 rounded-none border-2 border-cyber-border bg-cyber-card px-4 py-2 text-cyber-danger">
          <Heart width={18} height={18} />
          {user?.current_hp}
        </span>
      </div>

      <div>
        <h2 className="mb-3 font-display text-sm text-gray-100">ХАРАКТЕРИСТИКИ</h2>
        <StatsOverview />
      </div>
    </div>
  )
}
