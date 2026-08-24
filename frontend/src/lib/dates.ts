const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/
const LATIN_DATE = /^(\d{2})\/(\d{2})\/(\d{4})$/

export function formatDate(value: string | null | undefined, fallback = 'No informada'): string {
  if (!value) return fallback
  const match = ISO_DATE.exec(value.slice(0, 10))
  if (!match) return value
  return `${match[3]}/${match[2]}/${match[1]}`
}

export function parseLatinDate(value: string): string | null {
  const match = LATIN_DATE.exec(value.trim())
  if (!match) return null
  const [, day, month, year] = match
  const candidate = new Date(Number(year), Number(month) - 1, Number(day))
  if (candidate.getFullYear() !== Number(year) || candidate.getMonth() !== Number(month) - 1 || candidate.getDate() !== Number(day)) return null
  return `${year}-${month}-${day}`
}

export function todayLocalDate(): string {
  const today = new Date()
  return [today.getFullYear(), String(today.getMonth() + 1).padStart(2, '0'), String(today.getDate()).padStart(2, '0')].join('-')
}

export function addCalendarDays(value: string, days: number): string {
  const match = ISO_DATE.exec(value)
  if (!match) throw new Error('Fecha inválida')
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]))
  date.setDate(date.getDate() + days)
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-')
}
