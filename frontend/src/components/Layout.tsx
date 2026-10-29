import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useApiKey } from '../context/ApiKeyContext'
import { inputClass } from './ui'

const links = [
  { to: '/', label: 'Отследить', end: true },
  { to: '/deals', label: 'Сделки', end: false },
  { to: '/blockchain', label: 'Блокчейн', end: false },
  { to: '/network', label: 'Сеть нод', end: false },
]

function ApiKeyControl() {
  const { apiKey, setApiKey } = useApiKey()
  const [open, setOpen] = useState(false)

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm text-slate-600 transition hover:bg-slate-100"
        aria-expanded={open}
      >
        <span className={`size-2 rounded-full ${apiKey ? 'bg-emerald-500' : 'bg-amber-400'}`} />
        {apiKey ? 'Режим редактирования' : 'Только просмотр'}
      </button>
      {open && (
        <div className="absolute right-0 z-10 mt-2 w-72 rounded-xl border border-slate-200 bg-white p-4 shadow-lg">
          <label className="block text-sm">
            <span className="mb-1 block font-medium text-slate-700">API-ключ</span>
            <input
              type="password"
              className={inputClass}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="X-API-Key"
              autoComplete="off"
            />
          </label>
          <p className="mt-2 text-xs text-slate-500">
            Нужен для создания сделок и смены статусов. Значение по умолчанию на бэкенде —{' '}
            <code className="rounded bg-slate-100 px-1">change-me</code>.
          </p>
        </div>
      )}
    </div>
  )
}

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div className="flex flex-wrap items-center gap-3 sm:gap-8">
            <NavLink to="/" className="text-lg font-bold tracking-tight text-slate-900">
              Car<span className="text-brand-500">Leon</span>
            </NavLink>
            <nav className="flex flex-wrap gap-1">
              {links.map((l) => (
                <NavLink
                  key={l.to}
                  to={l.to}
                  end={l.end}
                  className={({ isActive }) =>
                    `rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                      isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-100'
                    }`
                  }
                >
                  {l.label}
                </NavLink>
              ))}
            </nav>
          </div>
          <ApiKeyControl />
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 py-5 text-center text-xs text-slate-400">
        CarLeon — перевозка автомобилей из-за рубежа
      </footer>
    </div>
  )
}
