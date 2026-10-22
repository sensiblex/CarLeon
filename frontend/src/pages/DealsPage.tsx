import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { StatusBadge } from '../components/StatusBadge'
import {
  buttonClass,
  Card,
  ErrorBox,
  Field,
  ghostButtonClass,
  inputClass,
  Spinner,
} from '../components/ui'
import { useApiKey } from '../context/ApiKeyContext'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import type { DealCreate } from '../types'
import { formatDate } from '../utils/format'

const empty: DealCreate = { track_code: '', title: '', supplier: '', buyer: '' }

function CreateDealForm({ onCancel }: { onCancel: () => void }) {
  const { apiKey } = useApiKey()
  const navigate = useNavigate()
  const [form, setForm] = useState<DealCreate>(empty)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const set = (key: keyof DealCreate) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const deal = await api.createDeal(
        {
          track_code: form.track_code.trim(),
          title: form.title.trim(),
          supplier: form.supplier.trim(),
          buyer: form.buyer.trim(),
        },
        apiKey,
      )
      navigate(`/deals/${encodeURIComponent(deal.track_code)}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать сделку')
      setSaving(false)
    }
  }

  return (
    <Card title="Новая сделка">
      <form onSubmit={onSubmit} className="grid gap-4 sm:grid-cols-2">
        <Field label="Трек-код" hint="От 4 до 32 символов, уникальный">
          <input className={inputClass} value={form.track_code} onChange={set('track_code')} required minLength={4} maxLength={32} />
        </Field>
        <Field label="Автомобиль">
          <input className={inputClass} value={form.title} onChange={set('title')} placeholder="BMW X5, 2022" required maxLength={255} />
        </Field>
        <Field label="Поставщик">
          <input className={inputClass} value={form.supplier} onChange={set('supplier')} required maxLength={128} />
        </Field>
        <Field label="Заказчик">
          <input className={inputClass} value={form.buyer} onChange={set('buyer')} required maxLength={128} />
        </Field>

        {!apiKey && (
          <p className="text-sm text-amber-700 sm:col-span-2">
            Для создания сделки укажите API-ключ в правом верхнем углу.
          </p>
        )}
        {error && (
          <div className="sm:col-span-2">
            <ErrorBox message={error} />
          </div>
        )}
        <div className="flex gap-2 sm:col-span-2">
          <button type="submit" className={buttonClass} disabled={saving || !apiKey}>
            {saving ? 'Создаём…' : 'Создать'}
          </button>
          <button type="button" className={ghostButtonClass} onClick={onCancel}>
            Отмена
          </button>
        </div>
      </form>
    </Card>
  )
}

export function DealsPage() {
  const { data, error, loading, reload } = useAsync(() => api.listDeals(), [])
  const [creating, setCreating] = useState(false)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Сделки</h1>
        {!creating && (
          <button className={buttonClass} onClick={() => setCreating(true)}>
            + Новая сделка
          </button>
        )}
      </div>

      {creating && <CreateDealForm onCancel={() => setCreating(false)} />}

      {loading && <Spinner />}
      {error && <ErrorBox message={error} onRetry={reload} />}

      {data && data.length === 0 && (
        <div className="rounded-xl border border-dashed border-slate-300 py-14 text-center text-sm text-slate-500">
          Сделок пока нет. Создайте первую.
        </div>
      )}

      {data && data.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-100 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3 font-medium">Трек-код</th>
                <th className="px-4 py-3 font-medium">Автомобиль</th>
                <th className="px-4 py-3 font-medium">Поставщик → Заказчик</th>
                <th className="px-4 py-3 font-medium">Статус</th>
                <th className="px-4 py-3 font-medium">Создана</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.map((d) => (
                <tr key={d.id} className="transition hover:bg-slate-50">
                  <td className="px-4 py-3 font-mono text-xs">
                    <Link to={`/deals/${encodeURIComponent(d.track_code)}`} className="font-medium text-brand-600 hover:underline">
                      {d.track_code}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{d.title}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {d.supplier} → {d.buyer}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={d.status} />
                  </td>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-500">{formatDate(d.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
