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
import { AuditPanel } from './components/AuditPanel'
import { ChatPanel } from './components/ChatPanel'
import { DocumentsPanel } from './components/DocumentsPanel'
import { LoginScreen } from './components/LoginScreen'
import { OverviewPanel } from './components/OverviewPanel'
import { ShellHeader } from './components/ShellHeader'
import { WorkspaceSidebar } from './components/WorkspaceSidebar'
import { WorkspaceTabs } from './components/WorkspaceTabs'
import {
  buildMemoryPrompt,
  createId,
} from './components/workspace-helpers'
import { panelLabels, type ChatTurn, type LoginMode, type Panel, type ThemeMode } from './components/workspace-model'
import type {
  AuditEventRecord,
  AuthSession,
  ConfigInfo,
  CurrentUser,
  DocumentRecord,
  GuardrailCheckResponse,
  HealthResponse,
  QueryResponse,
  RuntimeStats,
} from './types'

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
  const panelItems = (Object.entries(panelLabels) as Array<[Panel, string]>).map(([id, label]) => ({
    id,
    label,
  }))

  return (
    <div className="app-frame">
      <ShellHeader
        config={config}
        hasSession={hasSession}
        user={user}
        theme={theme}
        onToggleTheme={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        onLogout={startLogout}
      />

      {configError && <div className="alert alert--error">{configError}</div>}
      {uploadMessage && <div className="alert alert--success">{uploadMessage}</div>}
      {workspaceError && <div className="alert alert--warning">{workspaceError}</div>}

      {!hasSession ? (
        <LoginScreen
          config={config}
          loadingConfig={loadingConfig}
          loginMode={loginMode}
          username={username}
          password={password}
          apiKey={apiKey}
          authError={authError}
          authLoading={authLoading}
          onSubmit={handleLogin}
          onLoginModeChange={setLoginMode}
          onUsernameChange={setUsername}
          onPasswordChange={setPassword}
          onApiKeyChange={setApiKey}
        />
      ) : (
        <div className="workspace-layout">
          <WorkspaceSidebar
            user={user}
            retrievalHealth={retrievalHealth}
            providerHealth={providerHealth}
            runtimeStats={runtimeStats}
            workspaceLoading={workspaceLoading}
          />

          <main className="content">
            <WorkspaceTabs activePanel={activePanel} panels={panelItems} onPanelChange={setActivePanel} />

            {activePanel === 'overview' && (
              <OverviewPanel
                documentStats={documentStats}
                runtimeStats={runtimeStats}
                retrievalHealth={retrievalHealth}
                providerHealth={providerHealth}
              />
            )}

            {activePanel === 'documents' && (
              <DocumentsPanel
                documentStats={documentStats}
                selectedFiles={selectedFiles}
                uploading={uploading}
                uploadProgress={uploadProgress}
                uploadError={uploadError}
                documents={documents}
                onUpload={handleUpload}
                onFilesChange={setSelectedFiles}
                onDeleteDocument={(document) => void handleDeleteDocument(document)}
              />
            )}

            {activePanel === 'chat' && (
              <ChatPanel
                topK={topK}
                question={question}
                guardrailPreview={guardrailPreview}
                chatError={chatError}
                querying={querying}
                displayedAnswer={displayedAnswer}
                currentResponse={currentResponse}
                chatTurns={chatTurns}
                onAskQuestion={handleAskQuestion}
                onQuestionChange={setQuestion}
                onTopKChange={setTopK}
              />
            )}

            {activePanel === 'audit' && (
              <AuditPanel
                auditFilter={auditFilter}
                filteredAuditEvents={filteredAuditEvents}
                onAuditFilterChange={setAuditFilter}
              />
            )}
          </main>
        </div>
      )}

      {loadingConfig && <div className="screen-note">Loading app configuration…</div>}
    </div>
  )
}

export default App
