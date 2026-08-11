import { Zap, Wind, Cpu, Target, Heart } from 'pixelarticons/react'

export const statStyle = {
  Сила: {
    bar: 'bg-cyber-primary', text: 'text-cyber-primary', border: 'border-cyber-primary', icon: Zap,
    accent: 'var(--color-cyber-primary)',
  },
  Ловкость: {
    bar: 'bg-cyber-accent', text: 'text-cyber-accent', border: 'border-cyber-accent', icon: Wind,
    accent: 'var(--color-cyber-accent)',
  },
  Интелект: {
    bar: 'bg-cyber-secondary', text: 'text-cyber-secondary', border: 'border-cyber-secondary', icon: Cpu,
    accent: 'var(--color-cyber-secondary)',
  },
  Фокус: {
    bar: 'bg-cyber-cyan', text: 'text-cyber-cyan', border: 'border-cyber-cyan', icon: Target,
    accent: 'var(--color-cyber-cyan)',
  },
  Здоровье: {
    bar: 'bg-cyber-pink', text: 'text-cyber-pink', border: 'border-cyber-pink', icon: Heart,
    accent: 'var(--color-cyber-pink)',
  },
}

export const defaultStatStyle = {
  bar: 'bg-cyber-secondary',
  text: 'text-cyber-secondary',
  border: 'border-cyber-secondary',
  icon: Zap,
  accent: 'var(--color-cyber-secondary)',
}
