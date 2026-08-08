// Часовой пояс определяет, где для игрока проходит граница суток: когда
// сбрасываются ежедневки, засчитывается серия и открывается окно боя.

export const FALLBACK_TIMEZONE = 'UTC'

// Пояс браузера в формате IANA ("Europe/Moscow") — именно его ждёт бэкенд.
export function detectTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || FALLBACK_TIMEZONE
  } catch {
    return FALLBACK_TIMEZONE
  }
}

// "GMT+3" для подписи в интерфейсе: одно имя зоны мало что говорит игроку.
export function offsetLabel(timeZone) {
  try {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone,
      timeZoneName: 'shortOffset',
    }).formatToParts(new Date())
    return parts.find((p) => p.type === 'timeZoneName')?.value ?? ''
  } catch {
    return ''
  }
}

export function timezoneLabel(timeZone) {
  const offset = offsetLabel(timeZone)
  return offset ? `${timeZone} (${offset})` : timeZone
}

// Полный список зон берём у браузера. Intl.supportedValuesOf появился не
// везде, поэтому при его отсутствии оставляем хотя бы текущую и UTC —
// выпадающий список не должен оказаться пустым.
export function listTimezones(current) {
  const known = new Set([FALLBACK_TIMEZONE, detectTimezone()])
  if (current) known.add(current)

  try {
    for (const zone of Intl.supportedValuesOf('timeZone')) known.add(zone)
  } catch {
    // старый браузер — обходимся коротким списком
  }

  return [...known].sort().map((zone) => ({ value: zone, label: timezoneLabel(zone) }))
}
