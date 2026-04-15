import axios from 'axios'

import type {
  AuditEventListResponse,
  AuthSession,
  ConfigInfo,
  CurrentUser,
  DocumentRecord,
  DocumentBatchUploadResponse,
  GuardrailCheckResponse,
  HealthResponse,
  QueryResponse,
  QueryStreamEvent,
  RuntimeStats,
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

function queryHeaders(session: AuthSession | null) {
  return {
    'Content-Type': 'application/json',
    ...authHeaders(session),
  }
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
  files: File[],
  onProgress?: (percent: number) => void,
) {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  const { data } = await api.post<DocumentBatchUploadResponse>('/documents/upload', formData, {
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

export async function streamQueryDocuments(
  session: AuthSession,
  question: string,
  topK: number,
  onDelta?: (delta: string) => void,
) {
  const response = await fetch('/api/v1/query/stream', {
    method: 'POST',
    headers: queryHeaders(session),
    body: JSON.stringify({ question, top_k: topK }),
  })

  if (!response.ok) {
    throw new Error(await response.text())
  }

  if (!response.body) {
    throw new Error('Streaming is not supported in this browser.')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let finalResponse: QueryResponse | null = null

  const consumeLine = (line: string) => {
    if (!line.trim()) {
      return
    }

    const event = JSON.parse(line) as QueryStreamEvent
    if (event.type === 'delta') {
      onDelta?.(event.delta)
      return
    }

    finalResponse = event.response
  }

  for (;;) {
    const { value, done } = await reader.read()
    if (value) {
      buffer += decoder.decode(value, { stream: !done })
    }

    let newlineIndex = buffer.indexOf('\n')
    while (newlineIndex >= 0) {
      const line = buffer.slice(0, newlineIndex)
      buffer = buffer.slice(newlineIndex + 1)
      consumeLine(line)
      newlineIndex = buffer.indexOf('\n')
    }

    if (done) {
      break
    }
  }

  buffer += decoder.decode()

  const remainder = buffer.trim()
  if (remainder) {
    consumeLine(remainder)
  }

  if (!finalResponse) {
    throw new Error('Stream ended without a final response.')
  }

  return finalResponse
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

export async function getRuntimeStats(session: AuthSession) {
  const { data } = await api.get<RuntimeStats>('/stats', {
    headers: authHeaders(session),
  })
  return data
}
