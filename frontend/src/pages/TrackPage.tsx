import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { STATUSES } from '../utils/status'
import { buttonClass, inputClass } from '../components/ui'

export function TrackPage() {
  const [code, setCode] = useState('')
  const navigate = useNavigate()

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = code.trim()
    if (trimmed) navigate(`/deals/${encodeURIComponent(trimmed)}`)
  }

  return (
    <div className="mx-auto max-w-2xl py-10 text-center">
      <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
        Где сейчас ваш автомобиль?
      </h1>
      <p className="mt-3 text-slate-600">
        Введите трек-код сделки и посмотрите каждый этап — от покупки за рубежом до выдачи ключей.
        История статусов защищена блокчейном и не может быть изменена задним числом.
      </p>

      <form onSubmit={onSubmit} className="mt-8 flex gap-2">
        <input
          className={`${inputClass} py-3 text-base`}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Трек-код, например CL-2026-001"
          aria-label="Трек-код"
          autoFocus
        />
        <button type="submit" className={`${buttonClass} px-6`} disabled={!code.trim()}>
          Найти
        </button>
      </form>

      <div className="mt-14 text-left">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Этапы сделки
        </h2>
        <ol className="mt-4 grid gap-2 sm:grid-cols-2">
          {STATUSES.map((s, i) => (
            <li
              key={s}
              className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700"
            >
              <span className="flex size-6 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
                {i + 1}
              </span>
              {s}
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
