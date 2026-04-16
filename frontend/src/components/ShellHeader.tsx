import type { ConfigInfo, CurrentUser } from '../types'
import type { ThemeMode } from './workspace-model'

interface ShellHeaderProps {
  config: ConfigInfo | null
  hasSession: boolean
  user: CurrentUser | null
  theme: ThemeMode
  onToggleTheme: () => void
  onLogout: () => void
}

export function ShellHeader({
  config,
  hasSession,
  user,
  theme,
  onToggleTheme,
  onLogout,
}: ShellHeaderProps) {
  return (
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
          onClick={onToggleTheme}
          aria-pressed={theme === 'light'}
        >
          {theme === 'dark' ? 'Light theme' : 'Dark theme'}
        </button>
        {hasSession && (
          <button type="button" className="button button--ghost" onClick={onLogout}>
            Sign out
          </button>
        )}
      </div>
    </header>
  )
}
