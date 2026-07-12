import { useState } from 'react'
import { Eye, EyeOff } from 'pixelarticons/react'

export default function PasswordInput({ className = '', ...props }) {
  const [visible, setVisible] = useState(false)

  return (
    <div className="relative">
      <input
        type={visible ? 'text' : 'password'}
        className={`w-full rounded-none bg-cyber-muted px-3 py-2 pr-10 text-gray-100 ${className}`}
        {...props}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-cyber-secondary"
        aria-label={visible ? 'Скрыть пароль' : 'Показать пароль'}
        tabIndex={-1}
      >
        {visible ? <EyeOff width={18} height={18} /> : <Eye width={18} height={18} />}
      </button>
    </div>
  )
}
