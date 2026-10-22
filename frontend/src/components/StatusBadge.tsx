import { LAST_STATUS, statusLabel } from '../utils/status'

export function StatusBadge({ status }: { status: number }) {
  const done = status === LAST_STATUS
  const cls = done
    ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
    : status === 0
      ? 'bg-slate-100 text-slate-600 ring-slate-200'
      : 'bg-brand-50 text-brand-700 ring-brand-100'
  return (
    <span
      className={`inline-flex items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${cls}`}
    >
      {statusLabel(status)}
    </span>
  )
}
