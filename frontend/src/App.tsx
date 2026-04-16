import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'

import {
  authenticateApiKey,
  checkGuardrails,
  deleteDocument,
  getAuditEvents,
  getConfig,
  getCurrentUser,
  getDocuments,
  getProviderHealth,
  getRetrievalHealth,
  loginWithPassword,
  getRuntimeStats,
  uploadDocument,
  streamQueryDocuments,
} from './api/client'
import type {
  AuditEventRecord,
  AuthSession,
  Citation,
  ConfigInfo,
  CurrentUser,
  DocumentRecord,
  GuardrailCheckResponse,
  HealthResponse,
  QueryResponse,
  RuntimeStats,
} from './types'

type Panel = 'overview' | 'documents' | 'chat' | 'audit'
type LoginMode = 'password' | 'api-key'
type ThemeMode = 'dark' | 'light'

interface ChatTurn {
  id: string
  question: string
  answer: string
  citations: Citation[]
  confidence: number
  disclaimer: string | null
  createdAt: string
}

const panelLabels: Record<Panel, string> = {
  overview: 'Overview',
  documents: 'Documents',
  chat: 'Chat',
  audit: 'Audit',
}

function createId() {
  return globalThis.crypto?.randomUUID?.() ?? `item_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatDuration(seconds: number) {
  const safeSeconds = Math.max(0, Math.floor(seconds))
  const hours = Math.floor(safeSeconds / 3600)
  const minutes = Math.floor((safeSeconds % 3600) / 60)
  const remainingSeconds = safeSeconds % 60

  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`
  }
  return `${remainingSeconds}s`
}

function safeDetailValue(value: unknown) {
  if (typeof value === 'string') {
    return value
  }

  try {
    return JSON.stringify(value)
  } catch {
    return 'unserializable'
  }
}

function buildMemoryPrompt(question: string, turns: ChatTurn[]) {
  const trimmed = question.trim()
  const recentTurns = turns.slice(0, 3)
  if (!recentTurns.length) {
    return trimmed
  }

  const memory = recentTurns
    .map((turn, index) => {
      const answerPreview = turn.answer.slice(0, 180)
      return `Turn ${index + 1}\nQuestion: ${turn.question}\nAnswer: ${answerPreview}`
    })
    .join('\n\n')

  return `Conversation memory:\n${memory}\n\nCurrent question:\n${trimmed}`
}

function App() {
  const [config, setConfig] = useState<ConfigInfo | null>(null)
  const [loadingConfig, setLoadingConfig] = useState(true)
  const [configError, setConfigError] = useState<string | null>(null)
  const [session, setSession] = useState<AuthSession | null>(null)
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [authLoading, setAuthLoading] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)
  const [loginMode, setLoginMode] = useState<LoginMode>('password')
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const storedTheme = window.localStorage.getItem('ai-doc-assistant.theme')
    return storedTheme === 'light' ? 'light' : 'dark'
  })
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('')
  const [apiKey, setApiKey] = useState('')

  const [activePanel, setActivePanel] = useState<Panel>('overview')
  const [workspaceLoading, setWorkspaceLoading] = useState(false)
  const [workspaceError, setWorkspaceError] = useState<string | null>(null)
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [auditEvents, setAuditEvents] = useState<AuditEventRecord[]>([])
  const [retrievalHealth, setRetrievalHealth] = useState<HealthResponse | null>(null)
  const [providerHealth, setProviderHealth] = useState<HealthResponse | null>(null)
  const [runtimeStats, setRuntimeStats] = useState<RuntimeStats | null>(null)

  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadMessage, setUploadMessage] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)

  const [question, setQuestion] = useState('')
  const [topK, setTopK] = useState(4)
  const [guardrailPreview, setGuardrailPreview] = useState<GuardrailCheckResponse | null>(null)
  const [chatError, setChatError] = useState<string | null>(null)
  const [querying, setQuerying] = useState(false)
  const [displayedAnswer, setDisplayedAnswer] = useState('')
  const [currentResponse, setCurrentResponse] = useState<QueryResponse | null>(null)
  const [chatTurns, setChatTurns] = useState<ChatTurn[]>([])

  const [auditFilter, setAuditFilter] = useState('')

  useEffect(() => {
    let cancelled = false

    const loadConfig = async () => {
      try {
        setLoadingConfig(true)
        setConfigError(null)
        const nextConfig = await getConfig()
        if (!cancelled) {
          setConfig(nextConfig)
        }
      } catch (error) {
        if (!cancelled) {
          setConfigError(error instanceof Error ? error.message : 'Unable to load configuration.')
        }
      } finally {
        if (!cancelled) {
          setLoadingConfig(false)
        }
      }
    }

    void loadConfig()

    return () => {
      cancelled = true
    }
  }, [])

  const refreshWorkspace = useCallback(async (nextSession: AuthSession) => {
    setWorkspaceLoading(true)
    setWorkspaceError(null)

    const [documentsResult, auditResult, retrievalResult, providerResult, runtimeResult] =
      await Promise.allSettled([
        getDocuments(nextSession),
        getAuditEvents(nextSession),
        getRetrievalHealth(),
        getProviderHealth(),
        getRuntimeStats(nextSession),
      ])

    if (documentsResult.status === 'fulfilled') {
      setDocuments(documentsResult.value)
    } else {
      setWorkspaceError('Documents could not be refreshed.')
    }

    if (auditResult.status === 'fulfilled') {
      setAuditEvents(auditResult.value)
    }

    if (retrievalResult.status === 'fulfilled') {
      setRetrievalHealth(retrievalResult.value)
    } else {
      setRetrievalHealth(null)
    }

    if (providerResult.status === 'fulfilled') {
      setProviderHealth(providerResult.value)
    } else {
      setProviderHealth(null)
    }

    if (runtimeResult.status === 'fulfilled') {
      setRuntimeStats(runtimeResult.value)
    } else {
      setRuntimeStats(null)
    }

    setWorkspaceLoading(false)
  }, [])

  useEffect(() => {
    let cancelled = false

    const validateSession = async () => {
      if (!session) {
        setUser(null)
        setDocuments([])
        setAuditEvents([])
        setRetrievalHealth(null)
        setProviderHealth(null)
        setRuntimeStats(null)
        setChatTurns([])
        return
      }

      try {
        setAuthLoading(true)
        const currentUser = await getCurrentUser(session)
        if (cancelled) {
          return
        }

        setUser(currentUser)
        await refreshWorkspace(session)
      } catch {
        if (!cancelled) {
          setSession(null)
          setUser(null)
          setDocuments([])
          setAuditEvents([])
          setRetrievalHealth(null)
          setProviderHealth(null)
          setChatTurns([])
        }
      } finally {
        if (!cancelled) {
          setAuthLoading(false)
        }
      }
    }

    void validateSession()

    return () => {
      cancelled = true
    }
  }, [refreshWorkspace, session, setChatTurns, setSession])

  useEffect(() => {
    if (!session || !question.trim()) {
      setGuardrailPreview(null)
      return
    }

    const prompt = buildMemoryPrompt(question, chatTurns)
    const timer = window.setTimeout(() => {
      void checkGuardrails(session, prompt, topK)
        .then((result) => setGuardrailPreview(result))
        .catch(() => setGuardrailPreview(null))
    }, 300)

    return () => window.clearTimeout(timer)
  }, [chatTurns, question, session, topK])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem('ai-doc-assistant.theme', theme)
  }, [theme])

  const filteredAuditEvents = useMemo(() => {
    const needle = auditFilter.trim().toLowerCase()
    if (!needle) {
      return auditEvents
    }

    return auditEvents.filter((event) =>
      [
        event.action,
        event.actor,
        event.outcome,
        event.resource_type,
        event.resource_id ?? '',
      ]
        .join(' ')
        .toLowerCase()
        .includes(needle),
    )
  }, [auditEvents, auditFilter])

  const documentStats = useMemo(() => {
    const readyDocuments = documents.filter(
      (document) =>
        document.status === 'completed' || document.status === 'warning' || document.status === 'ready',
    ).length
    return {
      total: documents.length,
      available: readyDocuments,
      indexedChunks: documents.reduce((count, document) => count + document.chunk_count, 0),
      duplicates: documents.filter((document) => document.duplicate_of).length,
    }
  }, [documents])

  const startLogout = () => {
    setSession(null)
    setUser(null)
    setDocuments([])
    setAuditEvents([])
    setRetrievalHealth(null)
    setProviderHealth(null)
    setRuntimeStats(null)
    setChatTurns([])
    setQuestion('')
    setGuardrailPreview(null)
    setCurrentResponse(null)
    setDisplayedAnswer('')
    setSelectedFiles([])
    setUploadMessage(null)
    setUploadError(null)
    setActivePanel('overview')
  }

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setAuthLoading(true)
    setAuthError(null)

    try {
      if (loginMode === 'password') {
        const token = await loginWithPassword(username.trim(), password)
        const nextSession: AuthSession = {
          kind: 'jwt',
          token: token.access_token,
          username: username.trim(),
          scopes: ['read', 'write', 'admin'],
        }
        const currentUser = await getCurrentUser(nextSession)
        nextSession.username = currentUser.username
        nextSession.scopes = currentUser.scopes
        setSession(nextSession)
        setUser(currentUser)
        await refreshWorkspace(nextSession)
        setActivePanel('overview')
      } else {
        const currentUser = await authenticateApiKey(apiKey.trim())
        const nextSession: AuthSession = {
          kind: 'api_key',
          token: apiKey.trim(),
          username: currentUser.username,
          scopes: currentUser.scopes,
        }
        setSession(nextSession)
        setUser(currentUser)
        await refreshWorkspace(nextSession)
        setActivePanel('overview')
      }
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : 'Unable to sign in.')
    } finally {
      setAuthLoading(false)
    }
  }

  const handleUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!session || !selectedFiles.length) {
      return
    }

    setUploading(true)
    setUploadProgress(0)
    setUploadError(null)
    setUploadMessage(null)

    const form = event.currentTarget

    try {
      const response = await uploadDocument(session, selectedFiles, setUploadProgress)
      setUploadMessage(response.message ?? 'Document uploaded.')
      setSelectedFiles([])
      await refreshWorkspace(session)
      form.reset()
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed.')
    } finally {
      setUploading(false)
      setUploadProgress(0)
    }
  }

  const handleDeleteDocument = async (document: DocumentRecord) => {
    if (!session) {
      return
    }

    const confirmed = window.confirm(`Delete ${document.original_filename}?`)
    if (!confirmed) {
      return
    }

    try {
      await deleteDocument(session, document.id)
      setUploadMessage(`${document.original_filename} deleted.`)
      await refreshWorkspace(session)
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Delete failed.')
    }
  }

  const handleAskQuestion = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!session || !question.trim()) {
      return
    }

    const prompt = buildMemoryPrompt(question, chatTurns)
    setChatError(null)
    setCurrentResponse(null)
    setDisplayedAnswer('')
    setQuerying(true)

    try {
      const assessment = await checkGuardrails(session, prompt, topK)
      setGuardrailPreview(assessment)

      if (!assessment.allowed) {
        setChatError(assessment.blockers[0] ?? 'Prompt blocked by guardrails.')
        setQuerying(false)
        return
      }

      const response = await streamQueryDocuments(session, prompt, topK, (delta) => {
        setDisplayedAnswer((current) => current + delta)
      })
      setCurrentResponse(response)
      setDisplayedAnswer(response.answer)
      setChatTurns((current) => [
        {
          id: createId(),
          question: question.trim(),
          answer: response.answer,
          citations: response.citations,
          confidence: response.confidence,
          disclaimer: response.disclaimer ?? null,
          createdAt: new Date().toISOString(),
        },
        ...current,
      ].slice(0, 10))
      setQuestion('')
      await refreshWorkspace(session)
    } catch (error) {
      setChatError(error instanceof Error ? error.message : 'Query failed.')
    } finally {
      setQuerying(false)
    }
  }

  const hasSession = session !== null && user !== null

  return (
    <div className="app-frame">
      <header className="shell-header panel">
        <div className="shell-header__copy">
          <p className="eyebrow">AI Document Assistant</p>
          <h1>Operator workspace</h1>
          <p className="muted">Retrieval, document control, streaming chat, audit history, and guardrails.</p>
        </div>
        <div className="shell-header__actions">
          {config && <div className="pill pill--neutral">{config.llm_provider} · {config.llm_model}</div>}
          {hasSession && user && <div className="pill pill--success">{user.username} · {user.auth_method}</div>}
          <button
            type="button"
            className="button button--ghost"
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            aria-pressed={theme === 'light'}
          >
            {theme === 'dark' ? 'Light theme' : 'Dark theme'}
          </button>
          {hasSession && (
            <button type="button" className="button button--ghost" onClick={startLogout}>
              Sign out
            </button>
          )}
        </div>
      </header>

      {configError && <div className="alert alert--error">{configError}</div>}
      {uploadMessage && <div className="alert alert--success">{uploadMessage}</div>}
      {workspaceError && <div className="alert alert--warning">{workspaceError}</div>}

      {!hasSession ? (
        <section className="login-layout">
          <div className="panel panel--intro">
            <p className="eyebrow">What this demo shows</p>
            <h2>Minimal operator flow</h2>
            <ul className="feature-list">
              <li>JWT and API-key auth</li>
              <li>Document upload, duplicate detection, and delete</li>
              <li>Guardrail preflight and cited answers</li>
              <li>Session memory and audit trail</li>
            </ul>
            {loadingConfig ? <p className="muted">Loading runtime config…</p> : null}
            {config && (
              <div className="stack">
                <div className="mini-stat">
                  <span>App</span>
                  <strong>
                    {config.app_name} v{config.version}
                  </strong>
                </div>
                <div className="mini-stat">
                  <span>Provider</span>
                  <strong>
                    {config.llm_provider} · {config.llm_model}
                  </strong>
                </div>
              </div>
            )}
          </div>

          <form className="panel form-panel" onSubmit={handleLogin}>
            <div className="panel__header">
              <div>
                <p className="eyebrow">Sign in</p>
                <h2>Enter the workspace</h2>
              </div>
              <div className="segmented-control" role="tablist" aria-label="Authentication mode">
                <button
                  type="button"
                  className={loginMode === 'password' ? 'segmented-control__item is-active' : 'segmented-control__item'}
                  onClick={() => setLoginMode('password')}
                >
                  JWT
                </button>
                <button
                  type="button"
                  className={loginMode === 'api-key' ? 'segmented-control__item is-active' : 'segmented-control__item'}
                  onClick={() => setLoginMode('api-key')}
                >
                  API key
                </button>
              </div>
            </div>

            {loginMode === 'password' ? (
              <>
                <label className="field">
                  <span>Username</span>
                  <input
                    value={username}
                    onChange={(event) => setUsername(event.target.value)}
                    autoComplete="username"
                  />
                </label>
                <label className="field">
                  <span>Password</span>
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="current-password"
                  />
                </label>
              </>
            ) : (
              <label className="field">
                <span>API key</span>
                <input value={apiKey} onChange={(event) => setApiKey(event.target.value)} />
              </label>
            )}

            {authError && <div className="alert alert--error">{authError}</div>}

            <button type="submit" className="button button--primary" disabled={authLoading}>
              {authLoading ? 'Signing in…' : 'Open workspace'}
            </button>
          </form>
        </section>
      ) : (
        <div className="workspace-layout">
          <aside className="sidebar panel">
            <div className="sidebar__section">
              <p className="eyebrow">Navigation</p>
              <div className="nav-list">
                {(Object.keys(panelLabels) as Panel[]).map((panel) => (
                  <button
                    key={panel}
                    type="button"
                    className={activePanel === panel ? 'nav-list__item is-active' : 'nav-list__item'}
                    onClick={() => setActivePanel(panel)}
                  >
                    {panelLabels[panel]}
                  </button>
                ))}
              </div>
            </div>

            <div className="sidebar__section">
              <p className="eyebrow">Session</p>
              {user && (
                <div className="stack">
                  <div className="mini-stat">
                    <span>Operator</span>
                    <strong>{user.username}</strong>
                  </div>
                  <div className="mini-stat">
                    <span>Scopes</span>
                    <strong>{user.scopes.join(', ')}</strong>
                  </div>
                </div>
              )}
            </div>

            <div className="sidebar__section">
              <p className="eyebrow">Health</p>
              <div className="stack">
                <div className="mini-stat">
                  <span>Retrieval</span>
                  <strong>{retrievalHealth?.status ?? 'unknown'}</strong>
                </div>
                <div className="mini-stat">
                  <span>Provider</span>
                  <strong>{providerHealth?.status ?? 'unknown'}</strong>
                </div>
              </div>
            </div>

            {workspaceLoading && <p className="muted">Refreshing workspace…</p>}
          </aside>

          <main className="content">
            {activePanel === 'overview' && (
              <section className="grid grid--overview">
                <StatCard
                  title="Documents"
                  value={documentStats.total}
                  note={`${documentStats.available} available`}
                />
                <StatCard
                  title="Chunks"
                  value={documentStats.indexedChunks}
                  note={`${documentStats.duplicates} duplicates`}
                />
                <StatCard
                  title="Runtime"
                  value={runtimeStats ? formatDuration(runtimeStats.uptime_seconds) : 'unknown'}
                  note={runtimeStats ? `since ${formatTimestamp(runtimeStats.started_at)}` : 'waiting for stats'}
                />
                <StatCard
                  title="Queries"
                  value={runtimeStats?.query_total ?? 0}
                  note={`${runtimeStats?.audit_events_total ?? 0} audit events`}
                />
                <StatCard
                  title="Guardrails"
                  value={runtimeStats?.blocked_queries_total ?? 0}
                  note={`${runtimeStats?.failed_logins_total ?? 0} login failures`}
                />
                <StatCard
                  title="Retrieval"
                  value={retrievalHealth?.status ?? 'unknown'}
                  note={`${retrievalHealth?.indexed_documents ?? 0} indexed docs`}
                />
                <StatCard
                  title="Provider"
                  value={providerHealth?.status ?? 'unknown'}
                  note={providerHealth?.model ?? 'not reported'}
                />
              </section>
            )}

            {activePanel === 'documents' && (
              <section className="stack stack--large">
                <div className="panel">
                  <div className="panel__header">
                    <div>
                      <p className="eyebrow">Document management</p>
                      <h2>Upload and curate source files</h2>
                    </div>
                    <span className="pill pill--neutral">{documentStats.total} total</span>
                  </div>

                  <form className="upload-form" onSubmit={handleUpload}>
                    <label className="field">
                      <span>Source files</span>
                      <input
                        type="file"
                        accept=".txt,.md,.markdown,.pdf,.docx"
                        multiple
                        onChange={(event) => setSelectedFiles(Array.from(event.target.files ?? []))}
                      />
                    </label>

                    <div className="upload-actions">
                      <button type="submit" className="button button--primary" disabled={!selectedFiles.length || uploading}>
                        {uploading ? `Uploading… ${uploadProgress}%` : 'Upload files'}
                      </button>
                      <span className="muted">
                        {selectedFiles.length
                          ? `${selectedFiles.length} file(s): ${selectedFiles.map((file) => file.name).join(', ')}`
                          : 'Choose one or more TXT, MD, PDF, or DOCX files.'}
                      </span>
                    </div>

                    {uploadError && <div className="alert alert--error">{uploadError}</div>}
                    {uploading && (
                      <div className="progress">
                        <div className="progress__bar" style={{ width: `${uploadProgress}%` }} />
                      </div>
                    )}
                  </form>
                </div>

                <div className="panel">
                  <div className="panel__header">
                    <h2>Registry</h2>
                    <span className="muted">Newest documents first</span>
                  </div>

                  <div className="table-wrap">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Document</th>
                          <th>Status</th>
                          <th>Chunks</th>
                          <th>Warnings</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {documents.map((document) => (
                          <tr key={document.id}>
                            <td>
                              <strong>{document.original_filename}</strong>
                              <div className="muted">
                                {formatBytes(document.size_bytes)} · {document.content_type}
                              </div>
                            </td>
                            <td>
                              <div className="stack stack--tiny">
                                <span className={`pill pill--status pill--${document.status}`}>{document.status}</span>
                                <span className="muted">Index: {document.index_status}</span>
                              </div>
                            </td>
                            <td>{document.chunk_count}</td>
                            <td>
                              {document.warnings.length ? (
                                <ul className="inline-list">
                                  {document.warnings.map((warning) => (
                                    <li key={warning} className="pill pill--warning">
                                      {warning}
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <span className="muted">None</span>
                              )}
                            </td>
                            <td>
                              <button
                                type="button"
                                className="button button--ghost"
                                onClick={() => void handleDeleteDocument(document)}
                              >
                                Delete
                              </button>
                            </td>
                          </tr>
                        ))}
                        {!documents.length && (
                          <tr>
                            <td colSpan={5} className="empty-state">
                              No documents uploaded yet.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </section>
            )}

            {activePanel === 'chat' && (
              <section className="grid grid--chat">
                <div className="panel">
                  <div className="panel__header">
                    <div>
                      <p className="eyebrow">Grounded chat</p>
                      <h2>Ask a question against the current corpus</h2>
                    </div>
                    <span className="pill pill--neutral">top_k {topK}</span>
                  </div>

                  <form className="stack" onSubmit={handleAskQuestion}>
                    <label className="field">
                      <span>Question</span>
                      <textarea
                        rows={6}
                        value={question}
                        onChange={(event) => setQuestion(event.target.value)}
                        placeholder="What does the policy say about remote work?"
                      />
                    </label>

                    <label className="field">
                      <span>Retrieval depth</span>
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={topK}
                        onChange={(event) => setTopK(Number(event.target.value))}
                      />
                    </label>

                    <div className="upload-actions">
                      <button type="submit" className="button button--primary" disabled={querying || !question.trim()}>
                        {querying ? 'Thinking…' : 'Ask assistant'}
                      </button>
                      <span className="muted">
                        The UI sends a memory-augmented prompt so follow-ups stay in context.
                      </span>
                    </div>

                    {guardrailPreview && (
                      <div
                        className={
                          guardrailPreview.allowed
                            ? 'guardrail guardrail--ok'
                            : 'guardrail guardrail--blocked'
                        }
                      >
                        <strong>Guardrails</strong>
                        <p>{guardrailPreview.recommended_action}</p>
                        {guardrailPreview.warnings.length > 0 && (
                          <ul>
                            {guardrailPreview.warnings.map((warning) => (
                              <li key={warning}>{warning}</li>
                            ))}
                          </ul>
                        )}
                        {guardrailPreview.blockers.length > 0 && (
                          <ul>
                            {guardrailPreview.blockers.map((blocker) => (
                              <li key={blocker}>{blocker}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}

                    {chatError && <div className="alert alert--error">{chatError}</div>}
                  </form>
                </div>

                <div className="panel stack stack--large">
                  <div>
                    <div className="panel__header">
                      <h2>Assistant answer</h2>
                      {currentResponse && (
                        <span className="pill pill--neutral">
                          {Math.round(currentResponse.confidence * 100)}% confidence
                        </span>
                      )}
                    </div>
                    <div className="answer-box">
                      {displayedAnswer || 'Your answer will appear here after a query.'}
                    </div>
                    {querying && <p className="muted answer-status">Streaming answer from the server…</p>}
                    {currentResponse?.disclaimer && (
                      <p className="muted answer-disclaimer">{currentResponse.disclaimer}</p>
                    )}
                  </div>

                  <div>
                    <h3>Citations</h3>
                    <div className="stack stack--small">
                      {currentResponse?.citations.map((citation) => (
                        <details key={`${citation.chunk_id ?? citation.source}-${citation.source}`} className="citation-card">
                          <summary className="citation-card__summary">
                            <div className="citation-card__summary-title">
                              <strong>{citation.source}</strong>
                              <span className="muted">
                                {citation.page ? `Page ${citation.page}` : 'No page'} ·{' '}
                                {Math.round(citation.relevance_score * 100)}%
                              </span>
                            </div>
                            <span className="pill pill--neutral">Expand</span>
                          </summary>
                          <div className="citation-card__body stack stack--small">
                            {citation.excerpt ? <p>{citation.excerpt}</p> : <p className="muted">No excerpt available.</p>}
                            <div className="stack stack--tiny">
                              <span className="muted">Chunk: {citation.chunk_id ?? 'unknown'}</span>
                              <span className="muted">Source: {citation.source}</span>
                            </div>
                          </div>
                        </details>
                      ))}
                      {!currentResponse?.citations.length && (
                        <p className="muted">No citations yet.</p>
                      )}
                    </div>
                  </div>

                  <div>
                    <h3>Session memory</h3>
                    <div className="stack stack--small">
                      {chatTurns.map((turn) => (
                        <article key={turn.id} className="memory-card">
                          <p>
                            <strong>Q:</strong> {turn.question}
                          </p>
                          <p>
                            <strong>A:</strong> {turn.answer.slice(0, 160)}
                          </p>
                          <p className="muted">{formatTimestamp(turn.createdAt)}</p>
                        </article>
                      ))}
                      {!chatTurns.length && <p className="muted">No previous turns in this session.</p>}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {activePanel === 'audit' && (
              <section className="panel stack stack--large">
                <div className="panel__header">
                  <div>
                    <p className="eyebrow">Audit history</p>
                    <h2>Server-side activity log</h2>
                  </div>
                  <span className="pill pill--neutral">{filteredAuditEvents.length} events</span>
                </div>

                <label className="field">
                  <span>Filter</span>
                  <input
                    value={auditFilter}
                    onChange={(event) => setAuditFilter(event.target.value)}
                    placeholder="Search action, actor, or outcome"
                  />
                </label>

                <div className="stack stack--small">
                  {filteredAuditEvents.map((event) => (
                    <article key={event.id} className="audit-card">
                      <div className="audit-card__header">
                        <strong>{event.action}</strong>
                        <span className={`pill pill--status pill--${event.outcome}`}>{event.outcome}</span>
                      </div>
                      <p className="muted">
                        {event.actor} · {event.auth_method} · {event.resource_type}
                        {event.resource_id ? ` · ${event.resource_id}` : ''}
                      </p>
                      <p>{formatTimestamp(event.created_at)}</p>
                      {Object.keys(event.details).length > 0 && (
                        <pre className="details-block">{safeDetailValue(event.details)}</pre>
                      )}
                    </article>
                  ))}
                  {!filteredAuditEvents.length && <p className="muted">No matching events.</p>}
                </div>
              </section>
            )}
          </main>
        </div>
      )}

      {loadingConfig && <div className="screen-note">Loading app configuration…</div>}
    </div>
  )
}

function StatCard({ title, value, note }: { title: string; value: string | number; note: string }) {
  return (
    <article className="panel stat-card">
      <p className="eyebrow">{title}</p>
      <strong>{value}</strong>
      <span className="muted">{note}</span>
    </article>
  )
}

export default App
