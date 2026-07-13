import { Link } from 'react-router-dom'
import { ArrowLeft } from 'pixelarticons/react'

export default function BackLink({ to = '/', children = 'Назад' }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-2 border-2 border-cyber-border bg-cyber-muted px-3 py-2 font-mono text-sm uppercase tracking-wide text-gray-300 pixel-shadow-ghost transition-all hover:scale-105 hover:border-cyber-secondary hover:text-cyber-secondary hover:brightness-110 active:translate-x-1 active:translate-y-1 active:scale-100 active:shadow-none"
    >
      <ArrowLeft width={16} height={16} />
      {children}
    </Link>
  )
}
