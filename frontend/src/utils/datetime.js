export function toDateInputValue(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function toTimeInputValue(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const pad = (n) => String(n).padStart(2, '0')
  return `${pad(date.getHours())}:${pad(date.getMinutes())}`
}

// Combines separate date + time inputs into a UTC ISO string for the backend.
// If no time was set, defaults to the end of that day — a deadline with just a
// date still means "by the end of that day", not midnight at its start.
export function fromDateAndTimeInputValue(dateValue, timeValue) {
  if (!dateValue) return null
  const time = timeValue ? `${timeValue}:00` : '23:59:59'
  return new Date(`${dateValue}T${time}`).toISOString()
}
