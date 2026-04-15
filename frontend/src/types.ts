export interface ConfigInfo {
  app_name: string
  version: string
  llm_provider: string
  llm_model: string
}

export interface CurrentUser {
  username: string
  auth_method: 'jwt' | 'api_key'
  scopes: string[]
}

export interface AuthSession {
  kind: 'jwt' | 'api_key'
  token: string
  username: string
  scopes: string[]
}

export interface DocumentRecord {
  id: string
  filename: string
  original_filename: string
  content_type: string
  size_bytes: number
  fingerprint: string
  status: string
  index_status: string
  source_path: string | null
  duplicate_of: string | null
  page_count: number
  chunk_count: number
  warnings: string[]
  error_message: string | null
  created_at: string
  updated_at: string
  indexed_at: string | null
}

export interface DocumentUploadResponse {
  document: DocumentRecord
  created: boolean
  duplicate: boolean
  chunks_created: number
  message?: string | null
}

export interface Citation {
  source: string
  page?: number | null
  chunk_id?: string | null
  relevance_score: number
  excerpt?: string | null
}

export interface QueryResponse {
  answer: string
  citations: Citation[]
  confidence: number
  finish_reason: string
  disclaimer?: string | null
}

export interface GuardrailCheckResponse {
  allowed: boolean
  risk_level: string
  warnings: string[]
  blockers: string[]
  recommended_action: string
}

export interface AuditEventRecord {
  id: string
  actor: string
  auth_method: string
  action: string
  resource_type: string
  resource_id: string | null
  outcome: string
  details: Record<string, unknown>
  created_at: string
}

export interface AuditEventListResponse {
  events: AuditEventRecord[]
}

export interface HealthResponse {
  healthy: boolean
  status: string
  provider?: string
  model?: string
  collection?: string
  persist_directory?: string
  indexed_chunks?: number
  indexed_documents?: number
  embedding_dimensions?: number
  error?: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}
