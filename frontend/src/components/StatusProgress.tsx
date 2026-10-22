import { STATUSES } from '../utils/status'

/** Полоса прогресса по всем 10 статусам жизненного цикла сделки. */
export function StatusProgress({ current }: { current: number }) {
  return (
    <ol className="grid gap-x-2 gap-y-3 sm:grid-cols-5">
      {STATUSES.map((label, i) => {
        const state = i < current ? 'done' : i === current ? 'current' : 'todo'
        return (
          <li key={label} className="flex items-start gap-2" aria-current={state === 'current' ? 'step' : undefined}>
            <span
              className={`mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold ${
                state === 'done'
                  ? 'bg-brand-500 text-white'
                  : state === 'current'
                    ? 'bg-white text-brand-600 ring-2 ring-brand-500'
                    : 'bg-slate-100 text-slate-400'
              }`}
            >
              {state === 'done' ? '✓' : i + 1}
            </span>
            <span
              className={`text-xs leading-5 ${
                state === 'todo' ? 'text-slate-400' : state === 'current' ? 'font-semibold text-slate-900' : 'text-slate-600'
              }`}
            >
              {label}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
