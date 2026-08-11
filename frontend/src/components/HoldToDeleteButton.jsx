import { useCallback, useRef, useState } from 'react'

const HOLD_MS = 2000

const sizes = {
  md: 'px-4 py-2',
  sm: 'px-3 py-1',
}

// Кнопка удаления, которую нужно удерживать — случайный тап её не спускает.
// Заливка идёт слева направо на CSS-transition (не raf/стейт на кадр), досрочный
// отпуск обнуляет её через тот же transition в обратную сторону.
export default function HoldToDeleteButton({
  onConfirm,
  disabled = false,
  size = 'md',
  className = '',
  children = 'Удалить',
}) {
  const [holding, setHolding] = useState(false)
  const timeoutRef = useRef(null)

  const cancel = useCallback(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = null
    setHolding(false)
  }, [])

  const start = useCallback(() => {
    if (disabled) return
    setHolding(true)
    timeoutRef.current = setTimeout(() => {
      timeoutRef.current = null
      setHolding(false)
      onConfirm()
    }, HOLD_MS)
  }, [disabled, onConfirm])

  return (
    <button
      type="button"
      disabled={disabled}
      onPointerDown={start}
      onPointerUp={cancel}
      onPointerLeave={cancel}
      onPointerCancel={cancel}
      onContextMenu={(e) => e.preventDefault()}
      className={`relative touch-none overflow-hidden rounded-none border-2 border-cyber-border bg-cyber-muted font-mono text-base uppercase tracking-wide text-gray-300 pixel-shadow-ghost transition-[filter] select-none hover:brightness-110 disabled:opacity-40 disabled:hover:brightness-100 ${sizes[size]} ${className}`}
    >
      <span
        className="absolute inset-y-0 left-0 bg-cyber-danger"
        style={{
          width: holding ? '100%' : '0%',
          transition: holding ? `width ${HOLD_MS}ms linear` : 'width 200ms ease-out',
        }}
        aria-hidden="true"
      />
      <span className="relative z-10">{children}</span>
    </button>
  )
}
