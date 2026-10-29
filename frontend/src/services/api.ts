import type {
  ApiResponse,
  Block,
  BlockReceipt,
  ChainDump,
  Deal,
  DealCreate,
  InvalidBlockEvidence,
  NetworkNodeInfo,
  PeerStatus,
  StatusChange,
  TrackingPoint,
  ValidationReport,
} from '../types'

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? '/api/v1'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function errorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object') {
    const b = body as { detail?: unknown; error?: unknown }
    if (typeof b.detail === 'string') return b.detail
    if (b.detail && typeof b.detail === 'object') {
      const detail = b.detail as { message?: unknown; errors?: unknown }
      const message = typeof detail.message === 'string' ? detail.message : ''
      const errors = Array.isArray(detail.errors)
        ? detail.errors
            .map((e) => (e && typeof e === 'object' && 'message' in e ? String(e.message) : ''))
            .filter(Boolean)
        : []
      return [message, ...errors].filter(Boolean).join(': ') || fallback
    }
    // Ошибки валидации FastAPI: detail — массив объектов
    if (Array.isArray(b.detail)) {
      return b.detail
        .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : ''))
        .filter(Boolean)
        .join('; ') || fallback
    }
    if (typeof b.error === 'string') return b.error
  }
  return fallback
}

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; apiKey?: string } = {},
): Promise<T> {
  const headers: Record<string, string> = {}
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (options.apiKey) headers['X-API-Key'] = options.apiKey

  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    })
  } catch {
    throw new ApiError('Не удалось связаться с сервером. Проверьте, что бэкенд запущен.', 0)
  }

  const json: unknown = await res.json().catch(() => null)
  if (!res.ok) {
    const fallback =
      res.status === 401 ? 'Неверный или отсутствующий API-ключ' : `Ошибка сервера (${res.status})`
    throw new ApiError(errorMessage(json, fallback), res.status)
  }
  return (json as ApiResponse<T>).data
}

export const api = {
  // Сделки
  listDeals: () => request<Deal[]>('/deals?limit=500'),
  getDeal: (trackCode: string) => request<Deal>(`/deals/${encodeURIComponent(trackCode)}`),
  createDeal: (payload: DealCreate, apiKey: string) =>
    request<Deal>('/deals', { method: 'POST', body: payload, apiKey }),
  deleteDeal: (trackCode: string, apiKey: string) =>
    request<{ deleted: string }>(`/deals/${encodeURIComponent(trackCode)}`, {
      method: 'DELETE',
      apiKey,
    }),

  // Трекинг
  listTracking: (trackCode: string) =>
    request<TrackingPoint[]>(`/deals/${encodeURIComponent(trackCode)}/tracking`),
  addTracking: (trackCode: string, status: number, comment: string | null, apiKey: string) =>
    request<TrackingPoint>(`/deals/${encodeURIComponent(trackCode)}/tracking`, {
      method: 'POST',
      body: { status, comment },
      apiKey,
    }),

  // Блокчейн
  getChain: () => request<ChainDump>('/blockchain'),
  validateChain: () => request<ValidationReport>('/blockchain/validate'),
  verifyFiles: () => request<ValidationReport>('/blockchain/files/verify'),
  dealHistory: (dealId: string) =>
    request<StatusChange[]>(`/blockchain/deals/${encodeURIComponent(dealId)}/history`),

  // Node-to-node network API
  getNodeInfo: (apiKey: string) =>
    request<NetworkNodeInfo>('/network/info', { apiKey }),
  getPeers: (apiKey: string) =>
    request<PeerStatus[]>('/network/peers', { apiKey }),
  getPeerInfo: (peerId: string, apiKey: string) =>
    request<PeerStatus>(`/network/peers/${encodeURIComponent(peerId)}/info`, { apiKey }),
  getPeerBlock: (peerId: string, hash: string, apiKey: string) =>
    request<Block>(`/network/peers/${encodeURIComponent(peerId)}/blocks/${encodeURIComponent(hash)}`, { apiKey }),
  sendBlock: (peerId: string, hash: string, apiKey: string) =>
    request<BlockReceipt>(
      `/network/peers/${encodeURIComponent(peerId)}/blocks/${encodeURIComponent(hash)}/send`,
      { method: 'POST', apiKey },
    ),
  probeInvalidBlock: (peerId: string, apiKey: string) =>
    request<InvalidBlockEvidence>(`/network/peers/${encodeURIComponent(peerId)}/invalid-block-demo`, {
      method: 'POST',
      apiKey,
    }),
  addStatusChange: (dealId: string, status: number, apiKey: string) =>
    request<{ tx_hash: string; block_index: number }>('/blockchain/status', {
      method: 'POST',
      body: { deal_id: dealId, status },
      apiKey,
    }),
}
