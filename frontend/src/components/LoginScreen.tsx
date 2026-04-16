import type { FormEvent } from 'react'

import type { ConfigInfo } from '../types'
import type { LoginMode } from './workspace-model'

interface LoginScreenProps {
  config: ConfigInfo | null
  loadingConfig: boolean
  loginMode: LoginMode
  username: string
  password: string
  apiKey: string
  authError: string | null
  authLoading: boolean
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onLoginModeChange: (mode: LoginMode) => void
  onUsernameChange: (value: string) => void
  onPasswordChange: (value: string) => void
  onApiKeyChange: (value: string) => void
}

export function LoginScreen({
  config,
  loadingConfig,
  loginMode,
  username,
  password,
  apiKey,
  authError,
  authLoading,
  onSubmit,
  onLoginModeChange,
  onUsernameChange,
  onPasswordChange,
  onApiKeyChange,
}: LoginScreenProps) {
  return (
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

      <form className="panel form-panel" onSubmit={onSubmit}>
        <div className="panel__header">
          <div>
            <p className="eyebrow">Sign in</p>
            <h2>Enter the workspace</h2>
          </div>
          <div className="segmented-control" role="tablist" aria-label="Authentication mode">
            <button
              type="button"
              className={loginMode === 'password' ? 'segmented-control__item is-active' : 'segmented-control__item'}
              onClick={() => onLoginModeChange('password')}
            >
              JWT
            </button>
            <button
              type="button"
              className={loginMode === 'api-key' ? 'segmented-control__item is-active' : 'segmented-control__item'}
              onClick={() => onLoginModeChange('api-key')}
            >
              API key
            </button>
          </div>
        </div>

        {loginMode === 'password' ? (
          <>
            <label className="field">
              <span>Username</span>
              <input value={username} onChange={(event) => onUsernameChange(event.target.value)} autoComplete="username" />
            </label>
            <label className="field">
              <span>Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => onPasswordChange(event.target.value)}
                autoComplete="current-password"
              />
            </label>
          </>
        ) : (
          <label className="field">
            <span>API key</span>
            <input value={apiKey} onChange={(event) => onApiKeyChange(event.target.value)} />
          </label>
        )}

        {authError && <div className="alert alert--error">{authError}</div>}

        <button type="submit" className="button button--primary" disabled={authLoading}>
          {authLoading ? 'Signing in…' : 'Open workspace'}
        </button>
      </form>
    </section>
  )
}
