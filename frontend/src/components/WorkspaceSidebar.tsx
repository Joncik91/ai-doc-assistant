import type { CurrentUser, HealthResponse, RuntimeStats } from '../types'
import { formatTimestamp } from './workspace-helpers'

interface WorkspaceSidebarProps {
  user: CurrentUser | null
  retrievalHealth: HealthResponse | null
  providerHealth: HealthResponse | null
  runtimeStats: RuntimeStats | null
  workspaceLoading: boolean
}

export function WorkspaceSidebar({
  user,
  retrievalHealth,
  providerHealth,
  runtimeStats,
  workspaceLoading,
}: WorkspaceSidebarProps) {
  return (
    <aside className="sidebar panel">
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
        <p className="eyebrow">System</p>
        <div className="stack">
          <div className="mini-stat">
            <span>Retrieval</span>
            <strong>{retrievalHealth?.status ?? 'unknown'}</strong>
          </div>
          <div className="mini-stat">
            <span>Provider</span>
            <strong>{providerHealth?.status ?? 'unknown'}</strong>
          </div>
          <div className="mini-stat">
            <span>Last activity</span>
            <strong>{runtimeStats?.last_activity_at ? formatTimestamp(runtimeStats.last_activity_at) : 'No recent activity'}</strong>
          </div>
        </div>
      </div>

      {workspaceLoading && <p className="muted">Refreshing workspace…</p>}
    </aside>
  )
}
