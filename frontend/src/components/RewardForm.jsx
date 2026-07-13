import { useState } from 'react'
import { useCreateReward } from '../hooks/useRewards'
import Button from './Button'

export default function RewardForm() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [cost, setCost] = useState('')
  const [unlockLevel, setUnlockLevel] = useState('')
  const [repeatable, setRepeatable] = useState(false)

  const { mutate, isPending, error } = useCreateReward()

  const handleSubmit = (e) => {
    e.preventDefault()
    mutate(
      {
        title,
        description: description || null,
        cost: Number(cost),
        unlock_level: Number(unlockLevel) || 0,
        repeatable,
      },
      {
        onSuccess: () => {
          setTitle('')
          setDescription('')
          setCost('')
          setUnlockLevel('')
          setRepeatable(false)
        },
      }
    )
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3 rounded-none border-2 border-cyber-border bg-cyber-card p-4"
    >
      <h2 className="font-display text-sm text-gray-300">НОВАЯ НАГРАДА</h2>

      <input
        type="text"
        placeholder="Название"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        className="w-full rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        required
      />
      <textarea
        placeholder="Описание (необязательно)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        className="w-full rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        rows={2}
      />

      <div className="flex gap-3">
        <input
          type="number"
          min="1"
          placeholder="Цена"
          value={cost}
          onChange={(e) => setCost(e.target.value)}
          className="w-1/2 rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
          required
        />
        <input
          type="number"
          min="0"
          placeholder="Уровень"
          value={unlockLevel}
          onChange={(e) => setUnlockLevel(e.target.value)}
          className="w-1/2 rounded-none bg-cyber-muted px-3 py-2 text-sm text-gray-100"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-300">
        <input
          type="checkbox"
          checked={repeatable}
          onChange={(e) => setRepeatable(e.target.checked)}
          className="h-4 w-4 shrink-0 rounded-none border-2 border-cyber-border bg-cyber-muted accent-cyber-secondary"
        />
        Можно покупать многократно
      </label>

      {error && <p className="text-sm text-cyber-danger">Не удалось создать награду</p>}

      <Button type="submit" variant="primary" disabled={isPending}>
        {isPending ? 'Создаём...' : 'Создать награду'}
      </Button>
    </form>
  )
}
