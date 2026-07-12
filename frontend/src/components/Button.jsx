const variants = {
  primary: 'bg-cyber-primary text-cyber-bg pixel-shadow-primary',
  secondary: 'bg-cyber-secondary text-cyber-bg pixel-shadow-secondary',
  accent: 'bg-cyber-accent text-cyber-bg pixel-shadow-accent',
  ghost: 'bg-cyber-muted text-gray-300 border-2 border-cyber-border pixel-shadow-ghost',
}

const sizes = {
  md: 'px-4 py-2',
  sm: 'px-3 py-1',
}

export default function Button({ variant = 'primary', size = 'md', className = '', children, ...props }) {
  return (
    <button
      className={`rounded-none font-mono text-base uppercase tracking-wide transition-all hover:scale-105 hover:brightness-110 active:translate-x-1 active:translate-y-1 active:scale-100 active:shadow-none disabled:opacity-40 disabled:hover:scale-100 disabled:hover:brightness-100 disabled:active:translate-x-0 disabled:active:translate-y-0 ${sizes[size]} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
