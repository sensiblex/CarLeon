import { useState } from 'react'
import { useApiKey } from '../context/ApiKeyContext'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import type {
  Block,
  BlockReceipt,
  InvalidBlockEvidence,
  NetworkNodeInfo,
  PeerStatus,
} from '../types'

interface DemoEvidence {
  peerId: string
  sourceBefore: NetworkNodeInfo
  receiverBefore: NetworkNodeInfo
  block: Block
  receipt?: BlockReceipt
  receivedBlock?: Block
  receiverAfter?: NetworkNodeInfo
  invalidBlock?: InvalidBlockEvidence
}

function shortHash(hash: string | null | undefined) {
  return hash ? `${hash.slice(0, 12)}...${hash.slice(-8)}` : '—'
}

function NodePanel({
  label,
  info,
  peer,
  accent,
}: {
  label: string
  info?: NetworkNodeInfo | null
  peer?: PeerStatus
  accent: 'orange' | 'blue'
}) {
  const dot = peer
    ? peer.reachable && peer.compatible && peer.node?.valid
      ? 'bg-emerald-400'
      : 'bg-rose-400'
    : info?.valid
      ? 'bg-emerald-400'
      : 'bg-amber-400'
  const color = accent === 'orange' ? 'text-orange-300' : 'text-sky-300'
  const shown = info ?? peer?.node

  return (
    <section className="relative overflow-hidden rounded-2xl border border-white/10 bg-[#14202a] p-5 text-white shadow-xl">
      <div className="absolute -right-12 -top-16 size-48 rounded-full border border-white/5" />
      <div className="absolute -right-5 -top-9 size-32 rounded-full border border-white/5" />
      <div className="relative flex items-start justify-between gap-3">
        <div>
          <p className={`font-mono text-[11px] uppercase tracking-[0.22em] ${color}`}>{label}</p>
          <h2 className="mt-2 text-2xl font-semibold">{shown?.node_id ?? peer?.peer_id ?? 'Не настроена'}</h2>
        </div>
        <span className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs">
          <span className={`size-2 rounded-full ${dot}`} />
          {peer
            ? !peer.reachable
              ? 'нет связи'
              : !peer.compatible
                ? 'несовместима'
                : peer.node?.valid
                  ? 'на связи · валидна'
                  : 'цепь невалидна'
            : shown?.valid
              ? 'цепь валидна'
              : 'ожидание'}
        </span>
      </div>
      {shown ? (
        <dl className="relative mt-6 grid grid-cols-2 gap-x-4 gap-y-4">
          <div>
            <dt className="text-xs text-slate-400">Блоков</dt>
            <dd className="mt-1 font-mono text-2xl tabular-nums">{shown.block_count}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-400">Высота</dt>
            <dd className="mt-1 font-mono text-2xl tabular-nums">{shown.height}</dd>
          </div>
          <div className="col-span-2">
            <dt className="text-xs text-slate-400">Хэш вершины</dt>
            <dd className="mt-1 break-all font-mono text-xs text-slate-200" title={shown.head_hash ?? ''}>
              {shortHash(shown.head_hash)}
            </dd>
          </div>
        </dl>
      ) : (
        <p className="relative mt-6 text-sm text-slate-300">
          {typeof peer?.error === 'string'
            ? peer.error
            : peer?.error?.message ?? 'Введите API-ключ и проверьте доступность узла.'}
        </p>
      )}
    </section>
  )
}

function EvidenceRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1 border-t border-slate-200 py-3 sm:grid-cols-[150px_1fr] sm:gap-4">
      <dt className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</dt>
      <dd className="break-all font-mono text-xs text-slate-800">{value}</dd>
    </div>
  )
}

export function NetworkPage() {
  const { apiKey } = useApiKey()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [evidence, setEvidence] = useState<DemoEvidence | null>(null)
  const overview = useAsync(async () => {
    const [local, peers] = await Promise.all([api.getNodeInfo(apiKey), api.getPeers(apiKey)])
    const firstPeer = peers[0]
    const peer = firstPeer ? await api.getPeerInfo(firstPeer.peer_id, apiKey) : undefined
    return { local, peer }
  }, [apiKey])

  async function runDemo() {
    if (!apiKey) {
      setError('Сначала укажите API-ключ в правом верхнем углу. Для docker-compose по умолчанию: change-me.')
      return
    }
    setBusy(true)
    setError(null)
    setEvidence(null)

    try {
      const sourceBefore = await api.getNodeInfo(apiKey)
      const peerStatuses = await api.getPeers(apiKey)
      const peerId = peerStatuses[0]?.peer_id
      if (!peerId) throw new Error('У этой ноды не настроен ни один peer.')

      const receiverStatus = await api.getPeerInfo(peerId, apiKey)
      if (!receiverStatus.reachable || !receiverStatus.compatible || !receiverStatus.node) {
        const reason = typeof receiverStatus.error === 'string'
          ? receiverStatus.error
          : receiverStatus.error?.message ?? 'узел недоступен или использует другую сеть'
        throw new Error(`Peer ${peerId}: ${reason}`)
      }
      const receiverBefore = receiverStatus.node
      if (!sourceBefore.valid || !receiverBefore.valid) {
        throw new Error('Демо остановлено: одна из локальных цепочек уже не проходит проверку.')
      }

      let block: Block | undefined
      if (sourceBefore.block_count === receiverBefore.block_count) {
        if (sourceBefore.head_hash !== receiverBefore.head_hash) {
          throw new Error('Высота нод одинаковая, но хэши вершин различаются: обнаружена ветка истории.')
        }
        const dealId = `network-demo-${Date.now()}`
        const created = await api.addStatusChange(dealId, 4, apiKey)
        const sourceChain = await api.getChain()
        block = sourceChain.chain[created.block_index]
        if (!block || block.hash !== created.tx_hash) {
          throw new Error('Не удалось подтвердить созданный блок чтением реальной цепочки Node A.')
        }
      } else if (sourceBefore.block_count > receiverBefore.block_count) {
        const sourceChain = await api.getChain()
        block = sourceChain.chain[receiverBefore.block_count]
        if (!block) throw new Error('Не найден первый блок, отсутствующий у принимающей ноды.')
      } else {
        throw new Error('Принимающая нода впереди отправителя. Автоматическое согласование веток не включено.')
      }

      const initialEvidence: DemoEvidence = {
        peerId,
        sourceBefore,
        receiverBefore,
        block,
      }
      setEvidence(initialEvidence)

      const receipt = await api.sendBlock(peerId, block.hash, apiKey)
      setEvidence({ ...initialEvidence, receipt })

      const receivedBlock = await api.getPeerBlock(peerId, block.hash, apiKey)
      const receiverAfter = (await api.getPeerInfo(peerId, apiKey)).node ?? undefined
      setEvidence({ ...initialEvidence, receipt, receivedBlock, receiverAfter })

      const invalidBlock = await api.probeInvalidBlock(peerId, apiKey)
      setEvidence({ ...initialEvidence, receipt, receivedBlock, receiverAfter, invalidBlock })
      overview.reload()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Сетевая демонстрация завершилась ошибкой.')
      overview.reload()
    } finally {
      setBusy(false)
    }
  }

  const block = evidence?.block
  const transaction = block?.transactions[0]

  return (
    <div className="space-y-7">
      <header className="relative overflow-hidden rounded-3xl bg-[#101a22] px-6 py-7 text-white sm:px-9 sm:py-9">
        <div className="absolute -right-20 -top-36 size-96 rounded-full border border-white/5" />
        <div className="absolute -right-4 -top-20 size-64 rounded-full border border-white/5" />
        <div className="relative max-w-3xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-orange-300">CARLEON / NETWORK LAB</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">Две ноды. Один проверяемый обмен.</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">
            Демо создаёт запись в цепочке Node A, отправляет подписанный хэшами блок Node B,
            запрашивает его обратно и показывает отказ принимающей ноды на поддельный блок.
            Здесь отображаются ответы API и фактические вершины обеих цепочек.
          </p>
        </div>
        <div className="relative mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-[11px] uppercase tracking-wider text-slate-400">
          <span>JSON over HTTP</span><span className="text-orange-300">●</span>
          <span>раздельные файлы</span><span className="text-orange-300">●</span>
          <span>SHA-256 validation</span>
        </div>
      </header>

      {overview.error && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          {overview.error} Проверьте API-ключ (для локального Compose: <code>change-me</code>).
        </div>
      )}
      {error && (
        <div role="alert" className="rounded-xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-900">
          {error}
        </div>
      )}

      <div className="grid gap-3 lg:grid-cols-[1fr_100px_1fr] lg:items-stretch">
        <NodePanel label="Узел-отправитель / локальный" info={overview.data?.local} accent="orange" />
        <div className="flex items-center justify-center py-2 lg:flex-col">
          <span className="hidden h-10 w-px bg-slate-300 lg:block" />
          <span className="grid size-12 place-items-center rounded-full border border-slate-300 bg-white font-mono text-lg text-slate-600 shadow-sm">
            ⇄
          </span>
          <span className="hidden h-10 w-px bg-slate-300 lg:block" />
        </div>
        <NodePanel label="Известный peer / получатель" peer={overview.data?.peer} accent="blue" />
      </div>

      <section className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:px-6">
        <div>
          <p className="font-semibold text-slate-900">Запустить сквозную проверку</p>
          <p className="mt-1 text-sm text-slate-600">
            Добавится реальная запись со статусом «В пути», после чего блок будет передан peer-узлу.
          </p>
        </div>
        <button
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-orange-500 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:opacity-50"
          onClick={runDemo}
          disabled={busy || overview.loading}
        >
          <span aria-hidden="true">{busy ? '◌' : '▶'}</span>
          {busy ? 'Выполняем обмен…' : 'Создать и передать блок'}
        </button>
      </section>

      {overview.loading && !overview.data && (
        <div className="py-4 text-sm text-slate-500" role="status">Опрашиваем локальную ноду и настроенные peer-узлы…</div>
      )}

      {evidence && (
        <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <header className="flex flex-wrap items-center justify-between gap-3 bg-[#eaf2f3] px-5 py-4 sm:px-6">
            <div>
              <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">ПРОТОКОЛЬНОЕ ДОКАЗАТЕЛЬСТВО</p>
              <h2 className="mt-1 text-lg font-semibold text-slate-900">Полученный блок и ответ peer-ноды</h2>
            </div>
            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-800">
              {evidence.receipt ? 'Блок принят и сохранён' : 'Блок создан; ожидает отправки'}
            </span>
          </header>
          <dl className="px-5 sm:px-6">
            <EvidenceRow label="Маршрут" value={`${evidence.sourceBefore.node_id} → ${evidence.peerId}`} />
            <EvidenceRow label="Состояние до" value={`Node A: ${evidence.sourceBefore.block_count} блоков / ${shortHash(evidence.sourceBefore.head_hash)} · Node B: ${evidence.receiverBefore.block_count} блоков / ${shortHash(evidence.receiverBefore.head_hash)}`} />
            <EvidenceRow label="Номер блока" value={`#${block?.index}`} />
            <EvidenceRow label="SHA-256 блока" value={block?.hash ?? ''} />
            <EvidenceRow label="previous_hash" value={block?.previous_hash ?? ''} />
            <EvidenceRow label="Реальная запись" value={transaction ? `${transaction.deal_id} · статус ${transaction.status} · tx hash ${transaction.content_hash}` : '—'} />
            {evidence.receipt && (
              <EvidenceRow
                label="Ответ на POST"
                value={`HTTP 200 · accepted=${evidence.receipt.accepted} · node=${evidence.receipt.node_id} · height=${evidence.receipt.index} · hash=${evidence.receipt.hash} · valid=${evidence.receipt.validation.valid}`}
              />
            )}
            {evidence.receivedBlock && (
              <EvidenceRow
                label="Повторный GET"
                value={`GET ${evidence.peerId}/blocks/${block?.hash} → получен hash=${evidence.receivedBlock.hash}; совпал с отправленным: ${evidence.receivedBlock.hash === block?.hash ? 'ДА' : 'НЕТ'}`}
              />
            )}
            {evidence.receiverAfter && (
              <EvidenceRow
                label="Вершина Node B"
                value={`${evidence.receiverAfter.block_count} блоков · ${shortHash(evidence.receiverAfter.head_hash)} · ${evidence.receiverAfter.head_hash === block?.hash ? 'совпадает с переданным блоком' : 'полученный блок не является вершиной'}`}
              />
            )}
          </dl>
          {evidence.invalidBlock && (
            <div className="mx-5 mb-5 mt-2 rounded-xl border border-rose-200 bg-rose-50 p-4 sm:mx-6">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-rose-950">Негативный сценарий: повреждённый блок отклонён</p>
                <span className="rounded-full bg-rose-100 px-3 py-1 font-mono text-xs text-rose-900">HTTP 422 · {evidence.invalidBlock.error.code}</span>
              </div>
              <p className="mt-2 break-all font-mono text-xs text-rose-900">
                Поддельный hash: {evidence.invalidBlock.rejected_hash}
              </p>
              {evidence.invalidBlock.error.errors?.map((item, index) => (
                <p key={`${item.type}-${index}`} className="mt-2 text-sm text-rose-900">
                  {item.type}: {item.message}
                </p>
              ))}
              <p className="mt-2 break-all font-mono text-xs text-rose-900">
                До отказа: {evidence.invalidBlock.receiver_before.block_count} блоков / {shortHash(evidence.invalidBlock.receiver_before.head_hash)}
                {' · '}после: {evidence.invalidBlock.receiver_after.block_count} блоков / {shortHash(evidence.invalidBlock.receiver_after.head_hash)}
              </p>
              <p className="mt-2 text-xs font-medium text-rose-800">
                Блок не попал в цепочку Node B: {evidence.invalidBlock.receiver_unchanged ? 'подтверждено' : 'не подтверждено'}.
              </p>
            </div>
          )}
        </section>
      )}

      <p className="text-xs leading-5 text-slate-500">
        Автоматической синхронизации нет: узел принимает только следующий блок с корректным индексом,
        хэшем и ссылкой на текущую вершину. «Демо отказа» доступно только при APP_ENV=dev/demo.
      </p>
    </div>
  )
}
