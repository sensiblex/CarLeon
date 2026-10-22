import { useState } from 'react'
import { buttonClass, Card, ErrorBox, Spinner } from '../components/ui'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import type { ValidationReport } from '../types'
import { formatUnix, shortHash } from '../utils/format'
import { statusLabel } from '../utils/status'

function ReportView({ title, report }: { title: string; report: ValidationReport }) {
  return (
    <div
      className={`rounded-lg border px-4 py-3 text-sm ${
        report.valid
          ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
          : 'border-red-200 bg-red-50 text-red-800'
      }`}
    >
      <p className="font-semibold">
        {title}: {report.valid ? 'всё в порядке' : `найдено проблем — ${report.errors.length}`}
      </p>
      {!report.valid && (
        <ul className="mt-2 list-disc space-y-1 pl-5">
          {report.errors.map((e, i) => (
            <li key={i}>
              {e.message}
              {e.block_index !== null && <span className="font-mono"> (блок #{e.block_index})</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function ChainPage() {
  const chain = useAsync(() => api.getChain(), [])
  const [reports, setReports] = useState<{ chain?: ValidationReport; files?: ValidationReport }>({})
  const [checking, setChecking] = useState(false)
  const [checkError, setCheckError] = useState<string | null>(null)

  async function runChecks() {
    setChecking(true)
    setCheckError(null)
    try {
      const [c, f] = await Promise.all([api.validateChain(), api.verifyFiles()])
      setReports({ chain: c, files: f })
    } catch (err) {
      setCheckError(err instanceof Error ? err.message : 'Проверка не удалась')
    } finally {
      setChecking(false)
    }
  }

  // Свежие блоки сверху
  const blocks = chain.data ? [...chain.data.chain].reverse() : []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Блокчейн</h1>
          <p className="mt-1 text-sm text-slate-600">
            Журнал смен статусов. Каждый блок хранит хэш предыдущего, поэтому подмена записи задним числом ломает цепочку.
          </p>
        </div>
        <button className={buttonClass} onClick={runChecks} disabled={checking}>
          {checking ? 'Проверяем…' : 'Проверить целостность'}
        </button>
      </div>

      {checkError && <ErrorBox message={checkError} />}
      {(reports.chain || reports.files) && (
        <div className="grid gap-3 sm:grid-cols-2">
          {reports.chain && <ReportView title="Цепочка блоков" report={reports.chain} />}
          {reports.files && <ReportView title="Прикреплённые файлы" report={reports.files} />}
        </div>
      )}

      {chain.loading && <Spinner />}
      {chain.error && <ErrorBox message={chain.error} onRetry={chain.reload} />}

      {chain.data && (
        <p className="text-sm text-slate-500">Блоков в цепочке: {chain.data.chain.length}</p>
      )}

      <div className="space-y-3">
        {blocks.map((b) => (
          <Card key={b.index}>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-semibold">Блок #{b.index}</p>
              <p className="text-xs text-slate-500">{formatUnix(b.timestamp)}</p>
            </div>
            <dl className="mt-2 grid gap-x-6 gap-y-1 text-xs sm:grid-cols-2">
              <div className="flex gap-2">
                <dt className="text-slate-500">Хэш</dt>
                <dd className="font-mono" title={b.hash}>{shortHash(b.hash, 10)}</dd>
              </div>
              <div className="flex gap-2">
                <dt className="text-slate-500">Предыдущий</dt>
                <dd className="font-mono" title={b.previous_hash}>{shortHash(b.previous_hash, 10)}</dd>
              </div>
            </dl>
            {b.transactions.length > 0 && (
              <ul className="mt-3 divide-y divide-slate-100 border-t border-slate-100 text-sm">
                {b.transactions.map((tx, i) => (
                  <li key={i} className="flex flex-wrap items-center justify-between gap-2 py-2">
                    <span>
                      <span className="font-medium">{statusLabel(tx.status)}</span>
                      <span className="text-slate-500"> · сделка </span>
                      <span className="font-mono text-xs text-slate-500" title={tx.deal_id}>
                        {shortHash(tx.deal_id, 6)}
                      </span>
                    </span>
                    {tx.file_path && (
                      <span className="text-xs text-slate-500" title={tx.file_hash ?? ''}>
                        📎 {tx.file_path}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Card>
        ))}
      </div>
    </div>
  )
}
