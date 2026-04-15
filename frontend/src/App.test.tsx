import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import * as api from './api/client'

vi.mock('./api/client', () => ({
  authenticateApiKey: vi.fn(),
  checkGuardrails: vi.fn(),
  deleteDocument: vi.fn(),
  getAuditEvents: vi.fn(),
  getConfig: vi.fn(),
  getCurrentUser: vi.fn(),
  getDocuments: vi.fn(),
  getProviderHealth: vi.fn(),
  getRetrievalHealth: vi.fn(),
  getRuntimeStats: vi.fn(),
  loginWithPassword: vi.fn(),
  queryDocuments: vi.fn(),
  streamQueryDocuments: vi.fn(),
  uploadDocument: vi.fn(),
}))

const mockedApi = vi.mocked(api)

describe('App', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.clearAllMocks()
  })

  function mockWorkspaceData() {
    mockedApi.getConfig.mockResolvedValue({
      app_name: 'AI Document Assistant',
      version: '0.1.0',
      llm_provider: 'deepseek',
      llm_model: 'deepseek-chat',
    })
    mockedApi.loginWithPassword.mockResolvedValue({
      access_token: 'jwt-token',
      token_type: 'bearer',
      expires_in: 3600,
    })
    mockedApi.getCurrentUser.mockResolvedValue({
      username: 'admin',
      auth_method: 'jwt',
      scopes: ['read', 'write', 'admin'],
    })
    mockedApi.getDocuments.mockResolvedValue([
      {
        id: 'doc_1',
        filename: 'policy.txt',
        original_filename: 'policy.txt',
        content_type: 'text/plain',
        size_bytes: 128,
        fingerprint: 'abc123',
        status: 'completed',
        index_status: 'indexed',
        source_path: '/tmp/policy.txt',
        duplicate_of: null,
        page_count: 0,
        chunk_count: 2,
        warnings: [],
        error_message: null,
        created_at: '2026-04-15T18:00:00Z',
        updated_at: '2026-04-15T18:00:00Z',
        indexed_at: '2026-04-15T18:00:01Z',
      },
    ])
    mockedApi.getAuditEvents.mockResolvedValue([])
    mockedApi.getRetrievalHealth.mockResolvedValue({
      healthy: true,
      status: 'ready',
      indexed_chunks: 2,
      indexed_documents: 1,
      embedding_dimensions: 256,
    })
    mockedApi.getProviderHealth.mockResolvedValue({
      healthy: true,
      status: 'ready',
      provider: 'deepseek',
      model: 'deepseek-chat',
    })
    mockedApi.getRuntimeStats.mockResolvedValue({
      generated_at: '2026-04-15T18:00:00Z',
      started_at: '2026-04-15T17:00:00Z',
      uptime_seconds: 3720,
      documents_total: 1,
      documents_ready: 1,
      indexed_documents: 1,
      chunks_total: 2,
      duplicate_documents: 0,
      ingestion_events_total: 1,
      audit_events_total: 1,
      query_total: 0,
      blocked_queries_total: 0,
      failed_logins_total: 0,
      distinct_actors: 1,
      last_activity_at: '2026-04-15T18:00:00Z',
    })
    mockedApi.uploadDocument.mockResolvedValue({
      processed_count: 2,
      created_count: 1,
      warning_count: 0,
      duplicate_count: 1,
      failed_count: 0,
      message: 'Processed 2 file(s): 1 created, 0 with warnings, 1 duplicates, 0 failed.',
      results: [
        {
          filename: 'policy-a.txt',
          document: {
            id: 'doc_2',
            filename: 'policy-a.txt',
            original_filename: 'policy-a.txt',
            content_type: 'text/plain',
            size_bytes: 120,
            fingerprint: 'abc124',
            status: 'completed',
            index_status: 'indexed',
            source_path: '/tmp/policy-a.txt',
            duplicate_of: null,
            page_count: 0,
            chunk_count: 2,
            warnings: [],
            error_message: null,
            created_at: '2026-04-15T18:10:00Z',
            updated_at: '2026-04-15T18:10:00Z',
            indexed_at: '2026-04-15T18:10:01Z',
          },
          created: true,
          duplicate: false,
          warning: false,
          chunks_created: 2,
          message: 'Document ingested.',
          error: null,
        },
        {
          filename: 'policy-b.txt',
          document: {
            id: 'doc_1',
            filename: 'policy-b.txt',
            original_filename: 'policy-b.txt',
            content_type: 'text/plain',
            size_bytes: 120,
            fingerprint: 'abc123',
            status: 'completed',
            index_status: 'indexed',
            source_path: '/tmp/policy-b.txt',
            duplicate_of: null,
            page_count: 0,
            chunk_count: 2,
            warnings: [],
            error_message: null,
            created_at: '2026-04-15T18:10:00Z',
            updated_at: '2026-04-15T18:10:00Z',
            indexed_at: '2026-04-15T18:10:01Z',
          },
          created: false,
          duplicate: true,
          warning: false,
          chunks_created: 0,
          message: 'Duplicate document ignored.',
          error: null,
        },
      ],
    })
  }

  async function signInWithPassword() {
    fireEvent.change(screen.getByLabelText(/Password/i), {
      target: { value: 'admin' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Open workspace/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Documents/i })).toBeInTheDocument()
    })
  }

  it('authenticates an operator and shows the document workspace', async () => {
    mockWorkspaceData()

    render(<App />)

    await screen.findByRole('button', { name: /Open workspace/i })
    await signInWithPassword()

    expect(screen.getByText('1h 2m')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Documents/i }))

    await waitFor(() => {
      expect(screen.getByText('policy.txt', { selector: '.data-table strong' })).toBeInTheDocument()
    })
    expect(window.localStorage.getItem('ai-doc-assistant.session')).toBeNull()
  })

  it('shows a grounded answer with citations and session memory', async () => {
    mockWorkspaceData()
    mockedApi.checkGuardrails.mockResolvedValue({
      allowed: true,
      risk_level: 'low',
      warnings: [],
      blockers: [],
      recommended_action: 'proceed',
    })
    let resolveStream!: (value: {
      answer: string
      citations: {
        source: string
        page?: number | null
        chunk_id?: string | null
        relevance_score: number
        excerpt?: string | null
      }[]
      confidence: number
      finish_reason: string
      disclaimer?: string | null
    }) => void
    mockedApi.streamQueryDocuments.mockImplementation((_session, _question, _topK, onDelta) => {
      onDelta?.('Remote work is allowed with manager approval.')
      return new Promise((resolve) => {
        resolveStream = resolve
      })
    })

    render(<App />)

    await screen.findByRole('button', { name: /Open workspace/i })
    await signInWithPassword()

    fireEvent.click(screen.getByRole('button', { name: /Chat/i }))
    fireEvent.change(screen.getByLabelText(/Question/i), {
      target: { value: 'What is the remote work policy?' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Ask assistant/i }))

    await waitFor(() => {
      expect(
        screen.getByText('Remote work is allowed with manager approval.', {
          selector: '.answer-box',
        }),
      ).toBeInTheDocument()
    })

    await act(async () => {
      resolveStream({
        answer: 'Remote work is allowed with manager approval.',
        citations: [
          {
            source: 'policy.txt',
            page: 1,
            chunk_id: 'chunk_1',
            relevance_score: 0.96,
            excerpt: 'Remote work is allowed with manager approval.',
          },
        ],
        confidence: 0.91,
        finish_reason: 'stop',
        disclaimer: 'This answer is based on retrieved documents and may not be 100% accurate.',
      })
    })

    await waitFor(() => {
      expect(screen.getByText('policy.txt', { selector: '.citation-card summary strong' })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('policy.txt', { selector: '.citation-card summary strong' }))
    expect(screen.getByText(/Chunk: chunk_1/)).toBeInTheDocument()
  })

  it('toggles between dark and light themes', async () => {
    mockWorkspaceData()

    render(<App />)

    await screen.findByRole('button', { name: /Open workspace/i })
    await signInWithPassword()

    fireEvent.click(screen.getByRole('button', { name: /Light theme/i }))
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })

  it('uploads multiple documents in one request', async () => {
    mockWorkspaceData()

    render(<App />)

    await screen.findByRole('button', { name: /Open workspace/i })
    await signInWithPassword()

    fireEvent.click(screen.getByRole('button', { name: /Documents/i }))

    const fileInput = screen.getByLabelText(/Source files/i)
    const firstFile = new File(['policy one'], 'policy-a.txt', { type: 'text/plain' })
    const secondFile = new File(['policy two'], 'policy-b.txt', { type: 'text/plain' })

    fireEvent.change(fileInput, { target: { files: [firstFile, secondFile] } })
    fireEvent.click(screen.getByRole('button', { name: /Upload files/i }))

    await waitFor(() => {
      expect(mockedApi.uploadDocument).toHaveBeenCalledTimes(1)
    })

    const [, uploadedFiles] = mockedApi.uploadDocument.mock.calls[0]
    expect(uploadedFiles).toHaveLength(2)
    expect(screen.getByText(/Processed 2 file\(s\)/i)).toBeInTheDocument()
  })
})
