export interface ApiResponse<T> {
  success: boolean
  data: T
}

export interface Deal {
  id: string
  track_code: string
  title: string
  supplier: string
  buyer: string
  status: number
  created_at: string
}

export interface DealCreate {
  track_code: string
  title: string
  supplier: string
  buyer: string
}

export interface TrackingPoint {
  id: string
  deal_id: string
  status: number
  comment: string | null
  tx_hash: string | null
  block_index: number | null
  created_at: string
}

export interface StatusChange {
  deal_id: string
  status: number
  timestamp: number
  file_path: string | null
  file_hash: string | null
  content_hash: string
}

export interface Block {
  index: number
  timestamp: number
  previous_hash: string
  hash: string
  transactions: StatusChange[]
}

export interface ChainDump {
  chain: Block[]
}

export interface ChainError {
  type: string
  message: string
  block_index: number | null
  tx_index: number | null
  expected: string | null
  actual: string | null
}

export interface ValidationReport {
  valid: boolean
  first_break?: ChainError | null
  errors: ChainError[]
}

export interface NetworkNodeInfo {
  node_id: string
  network_id: string
  genesis_hash: string | null
  block_count: number
  height: number
  head_hash: string | null
  valid: boolean
}

export interface PeerStatus {
  peer_id: string
  reachable: boolean
  compatible: boolean
  node: NetworkNodeInfo | null
  error: string | { code: string; message: string; details?: unknown } | null
}

export interface BlockReceipt {
  accepted: boolean
  node_id: string
  index: number
  hash: string
  block_count: number
  head_hash: string
  validation: ValidationReport
}

export interface InvalidBlockEvidence {
  accepted: boolean
  peer_id: string
  rejected_hash: string
  error: {
    code: string
    message: string
    errors?: ChainError[]
  }
  receiver_before: NetworkNodeInfo
  receiver_after: NetworkNodeInfo
  receiver_unchanged: boolean
}
