import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { StatusBadge } from '../components/StatusBadge'
import { StatusProgress } from '../components/StatusProgress'
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
import { formatDate, shortHash } from '../utils/format'
import { LAST_STATUS, STATUSES, statusLabel } from '../utils/status'

function AddStatusForm({
  trackCode,
  current,
  onAdded,
}: {
  trackCode: string
  current: number
  onAdded: () => void
}) {
  const { apiKey } = useApiKey()
  const [status, setStatus] = useState(Math.min(current + 1, LAST_STATUS))
  const [comment, setComment] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await api.addTracking(trackCode, status, comment.trim() || null, apiKey)
      setComment('')
      onAdded()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сменить статус')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card title="Сменить статус">
      <form onSubmit={onSubmit} className="space-y-4">
        <Field label="Новый статус">
          <select className={inputClass} value={status} onChange={(e) => setStatus(Number(e.target.value))}>
            {STATUSES.map((s, i) => (
              <option key={s} value={i}>
                {i}. {s}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Комментарий" hint="Необязательно, до 255 символов">
          <input className={inputClass} value={comment} onChange={(e) => setComment(e.target.value)} maxLength={255} />
        </Field>
        {!apiKey && <p className="text-sm text-amber-700">Укажите API-ключ в правом верхнем углу.</p>}
        {error && <ErrorBox message={error} />}
        <button type="submit" className={buttonClass} disabled={saving || !apiKey}>
          {saving ? 'Записываем в блокчейн…' : 'Записать статус'}
        </button>
      </form>
    </Card>
  )
}

export function DealPage() {
  const { trackCode = '' } = useParams()
  const navigate = useNavigate()
  const { apiKey } = useApiKey()

  const deal = useAsync(() => api.getDeal(trackCode), [trackCode])
  const points = useAsync(() => api.listTracking(trackCode), [trackCode])
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  function refresh() {
    deal.reload()
    points.reload()
  }

  async function onDelete() {
    if (!window.confirm(`Удалить сделку ${trackCode} вместе с историей трекинга?`)) return
    setDeleting(true)
    setDeleteError(null)
    try {
      await api.deleteDeal(trackCode, apiKey)
      navigate('/deals')
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Не удалось удалить')
      setDeleting(false)
    }
  }

  if (deal.loading && !deal.data) return <Spinner />
  if (deal.error || !deal.data) {
    return (
      <div className="space-y-4">
        <ErrorBox message={deal.error ?? 'Сделка не найдена'} onRetry={deal.reload} />
        <Link to="/" className="text-sm font-medium text-brand-600 hover:underline">
          ← Искать другой код
        </Link>
      </div>
    )
  }

  const d = deal.data
  // Новые точки сверху
  const history = [...(points.data ?? [])].reverse()

  return (
    <div className="space-y-6">
      <Link to="/deals" className="text-sm text-slate-500 hover:text-slate-800">
        ← Все сделки
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-mono text-xs text-slate-500">{d.track_code}</p>
          <h1 className="text-2xl font-bold tracking-tight">{d.title}</h1>
          <p className="mt-1 text-sm text-slate-600">
            {d.supplier} → {d.buyer} · создана {formatDate(d.created_at)}
          </p>
        </div>
        <StatusBadge status={d.status} />
      </div>

      <Card title="Ход сделки">
        <StatusProgress current={d.status} />
      </Card>

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <Card title="История статусов">
            {points.loading && !points.data && <Spinner />}
            {points.error && <ErrorBox message={points.error} onRetry={points.reload} />}
            {points.data && history.length === 0 && (
              <p className="text-sm text-slate-500">Пока нет записей о смене статуса.</p>
            )}
            <ol className="relative space-y-5 border-l border-slate-200 pl-6">
              {history.map((p, i) => (
                <li key={p.id} className="relative">
                  <span
                    className={`absolute -left-[31px] top-1 size-3 rounded-full ring-4 ring-white ${
                      i === 0 ? 'bg-brand-500' : 'bg-slate-300'
                    }`}
                  />
                  <p className="text-sm font-semibold text-slate-900">{statusLabel(p.status)}</p>
                  <p className="text-xs text-slate-500">{formatDate(p.created_at)}</p>
                  {p.comment && <p className="mt-1 text-sm text-slate-700">{p.comment}</p>}
                  {p.tx_hash && (
                    <p className="mt-1 text-xs text-slate-500">
                      Блок <span className="font-mono">#{p.block_index}</span> ·{' '}
                      <span className="font-mono" title={p.tx_hash}>
                        {shortHash(p.tx_hash)}
                      </span>
                    </p>
                  )}
                </li>
              ))}
            </ol>
          </Card>
        </div>

        <div className="space-y-6 lg:col-span-2">
          <AddStatusForm trackCode={d.track_code} current={d.status} onAdded={refresh} />
          <div>
            <button className={`${ghostButtonClass} text-red-700`} onClick={onDelete} disabled={deleting || !apiKey}>
              {deleting ? 'Удаляем…' : 'Удалить сделку'}
            </button>
            {deleteError && (
              <div className="mt-3">
                <ErrorBox message={deleteError} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
