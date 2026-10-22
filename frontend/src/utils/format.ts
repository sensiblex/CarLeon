const dateTime = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

/** ISO-строка от API (UTC) → читаемая дата */
export function formatDate(iso: string): string {
  // SQLite может отдавать время без часового пояса — считаем его UTC
  const normalized = /[zZ]|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : `${iso}Z`
  return dateTime.format(new Date(normalized))
}

/** Unix-время в секундах (как хранит блокчейн) → читаемая дата */
export function formatUnix(seconds: number): string {
  return dateTime.format(new Date(seconds * 1000))
}

export function shortHash(hash: string | null | undefined, len = 8): string {
  if (!hash) return '—'
  return hash.length > len * 2 ? `${hash.slice(0, len)}…${hash.slice(-len)}` : hash
}
