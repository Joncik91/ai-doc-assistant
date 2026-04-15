import axios from 'axios'

import type {
  AuditEventListResponse,
  AuthSession,
  ConfigInfo,
  CurrentUser,
  DocumentRecord,
  DocumentUploadResponse,
  GuardrailCheckResponse,
  HealthResponse,
  QueryResponse,
  TokenResponse,
} from '../types'

const api = axios.create({
  baseURL: '/api/v1',
})

function authHeaders(session: AuthSession | null) {
  if (!session) {
    return {}
  }

  if (session.kind === 'api_key') {
    return { 'X-API-Key': session.token }
  }

  return { Authorization: `Bearer ${session.token}` }
}

export async function getConfig() {
  const { data } = await api.get<ConfigInfo>('/config')
  return data
}

export async function loginWithPassword(username: string, password: string) {
  const { data } = await api.post<TokenResponse>('/auth/login', { username, password })
  return data
}

export async function authenticateApiKey(apiKey: string) {
  const { data } = await api.get<CurrentUser>('/auth/me', {
    headers: { 'X-API-Key': apiKey },
  })
  return data
}

export async function getCurrentUser(session: AuthSession) {
  const { data } = await api.get<CurrentUser>('/auth/me', {
    headers: authHeaders(session),
  })
  return data
}

export async function getDocuments(session: AuthSession) {
  const { data } = await api.get<{ documents: DocumentRecord[] }>('/documents', {
    headers: authHeaders(session),
  })
  return data.documents
}

export async function uploadDocument(
  session: AuthSession,
  file: File,
  onProgress?: (percent: number) => void,
) {
  const formData = new FormData()
  formData.append('file', file)

  const { data } = await api.post<DocumentUploadResponse>('/documents/upload', formData, {
    headers: authHeaders(session),
    onUploadProgress: (event) => {
      if (!onProgress || !event.total) {
        return
      }

      onProgress(Math.round((event.loaded / event.total) * 100))
    },
  })

  return data
}

export async function deleteDocument(session: AuthSession, documentId: string) {
  const { data } = await api.delete<{ document_id: string; deleted: boolean }>(
    `/documents/${documentId}`,
    {
      headers: authHeaders(session),
    },
  )
  return data
}

export async function checkGuardrails(
  session: AuthSession,
  question: string,
  topK: number,
) {
  const { data } = await api.post<GuardrailCheckResponse>(
    '/guardrails/check',
    { question, top_k: topK },
    { headers: authHeaders(session) },
  )
  return data
}

export async function queryDocuments(
  session: AuthSession,
  question: string,
  topK: number,
) {
  const { data } = await api.post<QueryResponse>(
    '/query',
    { question, top_k: topK },
    { headers: authHeaders(session) },
  )
  return data
}

export async function getAuditEvents(session: AuthSession, limit = 25) {
  const { data } = await api.get<AuditEventListResponse>('/audit/events', {
    headers: authHeaders(session),
    params: { limit },
  })
  return data.events
}

export async function getRetrievalHealth() {
  const { data } = await api.get<HealthResponse>('/health/retrieval')
  return data
}

export async function getProviderHealth() {
  const { data } = await api.get<HealthResponse>('/health/provider')
  return data
}
