import { useToastStore } from '../store/toastStore'

const typeStyles = {
  success: 'border-cyber-accent text-cyber-accent glow-accent',
  error: 'border-cyber-primary text-cyber-danger glow-primary',
  info: 'border-cyber-secondary text-cyber-secondary glow-secondary',
}

export default function ToastContainer() {
  const toasts = useToastStore((state) => state.toasts)
  const removeToast = useToastStore((state) => state.removeToast)
  const pauseToast = useToastStore((state) => state.pauseToast)
  const resumeToast = useToastStore((state) => state.resumeToast)

  return (
    <div role="status" aria-live="polite" className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <button
          key={toast.id}
          type="button"
          onClick={() => removeToast(toast.id)}
          onMouseEnter={() => pauseToast(toast.id)}
          onMouseLeave={() => resumeToast(toast.id)}
          onFocus={() => pauseToast(toast.id)}
          onBlur={() => resumeToast(toast.id)}
          className={`animate-toast-in rounded border bg-cyber-card px-4 py-3 text-left font-mono text-sm ${typeStyles[toast.type] ?? typeStyles.info}`}
        >
          {toast.message}
        </button>
      ))}
    </div>
  )
}
