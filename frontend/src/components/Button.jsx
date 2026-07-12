const variants = {
  primary: 'bg-cyber-primary text-white glow-primary',
  secondary: 'bg-cyber-secondary text-white glow-secondary',
  accent: 'bg-cyber-accent text-cyber-bg glow-accent',
  ghost: 'bg-cyber-muted text-gray-300 border border-cyber-border',
}

const sizes = {
  md: 'px-4 py-2',
  sm: 'px-3 py-1',
}

export default function Button({ variant = 'primary', size = 'md', className = '', children, ...props }) {
  return (
    <button
      className={`rounded text-sm font-medium transition-transform active:scale-95 disabled:opacity-40 disabled:active:scale-100 ${sizes[size]} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
