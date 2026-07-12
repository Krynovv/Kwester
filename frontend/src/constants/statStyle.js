import { Zap, Wind, Cpu, Target, Heart } from 'pixelarticons/react'

export const statStyle = {
  Сила: { bar: 'bg-cyber-primary', text: 'text-cyber-primary', border: 'border-cyber-primary', icon: Zap },
  Ловкость: { bar: 'bg-cyber-accent', text: 'text-cyber-accent', border: 'border-cyber-accent', icon: Wind },
  Интелект: { bar: 'bg-cyber-secondary', text: 'text-cyber-secondary', border: 'border-cyber-secondary', icon: Cpu },
  Фокус: { bar: 'bg-cyber-cyan', text: 'text-cyber-cyan', border: 'border-cyber-cyan', icon: Target },
  Здоровье: { bar: 'bg-cyber-pink', text: 'text-cyber-pink', border: 'border-cyber-pink', icon: Heart },
}

export const defaultStatStyle = {
  bar: 'bg-cyber-secondary',
  text: 'text-cyber-secondary',
  border: 'border-cyber-secondary',
  icon: Zap,
}
