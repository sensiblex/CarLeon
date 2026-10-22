import type {
  ApiResponse,
  ChainDump,
  Deal,
  DealCreate,
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
}
