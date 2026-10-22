// Статусы сделки — совпадают с DealStatus на бэкенде (0–9)
export const STATUSES = [
  'Опубликовано',
  'Заказ оформлен',
  'Оплачен депозит',
  'Выкуплен у продавца',
  'В пути (страна отправки)',
  'Таможня',
  'В пути (РФ)',
  'Доставлен в город',
  'Готов к выдаче',
  'Завершено',
] as const

export const LAST_STATUS = STATUSES.length - 1

export function statusLabel(status: number): string {
  return STATUSES[status] ?? `Статус ${status}`
}
