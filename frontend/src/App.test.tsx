import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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
  loginWithPassword: vi.fn(),
  queryDocuments: vi.fn(),
  uploadDocument: vi.fn(),
}))

const mockedApi = vi.mocked(api)

describe('App', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.clearAllMocks()
  })

  it('authenticates an operator and shows the document workspace', async () => {
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
        status: 'ready',
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

    render(<App />)

    await screen.findByRole('button', { name: /Open workspace/i })
    fireEvent.click(screen.getByRole('button', { name: /Open workspace/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Documents/i })).toBeInTheDocument()
    })

    fireEvent.click(screen.getByRole('button', { name: /Documents/i }))

    await waitFor(() => {
      expect(screen.getByText('policy.txt', { selector: '.data-table strong' })).toBeInTheDocument()
    })
  })

  it('shows a grounded answer with citations and session memory', async () => {
    window.localStorage.setItem(
      'ai-doc-assistant.session',
      JSON.stringify({
        kind: 'jwt',
        token: 'jwt-token',
        username: 'admin',
        scopes: ['read', 'write', 'admin'],
      }),
    )

    mockedApi.getConfig.mockResolvedValue({
      app_name: 'AI Document Assistant',
      version: '0.1.0',
      llm_provider: 'deepseek',
      llm_model: 'deepseek-chat',
    })
    mockedApi.getCurrentUser.mockResolvedValue({
      username: 'admin',
      auth_method: 'jwt',
      scopes: ['read', 'write', 'admin'],
    })
    mockedApi.getDocuments.mockResolvedValue([])
    mockedApi.getAuditEvents.mockResolvedValue([])
    mockedApi.getRetrievalHealth.mockResolvedValue({
      healthy: true,
      status: 'ready',
      indexed_chunks: 0,
      indexed_documents: 0,
      embedding_dimensions: 256,
    })
    mockedApi.getProviderHealth.mockResolvedValue({
      healthy: true,
      status: 'ready',
      provider: 'deepseek',
      model: 'deepseek-chat',
    })
    mockedApi.checkGuardrails.mockResolvedValue({
      allowed: true,
      risk_level: 'low',
      warnings: [],
      blockers: [],
      recommended_action: 'proceed',
    })
    mockedApi.queryDocuments.mockResolvedValue({
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

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Chat/i })).toBeInTheDocument()
    })

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
      expect(screen.getByText('policy.txt', { selector: '.citation-card strong' })).toBeInTheDocument()
    })
  })
})
