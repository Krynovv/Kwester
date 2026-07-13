import { useEffect, useRef, useState } from 'react'
import { ChevronDown } from 'pixelarticons/react'

export default function Select({ value, onChange, options, className = '' }) {
  const [open, setOpen] = useState(false)
  const [highlighted, setHighlighted] = useState(0)
  const rootRef = useRef(null)

  const selected = options.find((o) => o.value === value)
  const selectedIndex = options.findIndex((o) => o.value === value)

  useEffect(() => {
    if (!open) return
    const handleClick = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [open])

  const openList = () => {
    setHighlighted(selectedIndex >= 0 ? selectedIndex : 0)
    setOpen(true)
  }

  const handleKeyDown = (e) => {
    if (!open) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
        e.preventDefault()
        openList()
      }
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setHighlighted((i) => Math.min(i + 1, options.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlighted((i) => Math.max(i - 1, 0))
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onChange(options[highlighted].value)
      setOpen(false)
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div ref={rootRef} className={`relative ${className}`}>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => (open ? setOpen(false) : openList())}
        onKeyDown={handleKeyDown}
        className="flex w-full items-center justify-between bg-cyber-muted px-2 py-1.5 text-left text-sm text-gray-100 sm:px-3 sm:py-2 sm:text-base"
      >
        <span className="min-w-0 truncate">{selected?.label ?? ''}</span>
        <ChevronDown width={16} height={16} className="shrink-0 text-gray-400" />
      </button>

      {open && (
        <ul
          role="listbox"
          className="absolute z-40 mt-1 max-h-48 w-full overflow-auto bg-cyber-card sm:max-h-60"
        >
          {options.map((opt, i) => (
            <li
              key={opt.value}
              role="option"
              aria-selected={opt.value === value}
              onMouseEnter={() => setHighlighted(i)}
              onClick={() => {
                onChange(opt.value)
                setOpen(false)
              }}
              className={`cursor-pointer px-2 py-1.5 text-sm sm:px-3 sm:py-2 sm:text-base ${
                i === highlighted ? 'bg-cyber-secondary text-cyber-bg' : 'text-gray-100'
              }`}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
