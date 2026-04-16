import type { HealthResponse, RuntimeStats } from '../types'
import { formatDuration, formatTimestamp } from './workspace-helpers'

interface DocumentStats {
  total: number
  available: number
  indexedChunks: number
  duplicates: number
}

interface OverviewPanelProps {
  documentStats: DocumentStats
  runtimeStats: RuntimeStats | null
  retrievalHealth: HealthResponse | null
  providerHealth: HealthResponse | null
}

export function OverviewPanel({
  documentStats,
  runtimeStats,
  retrievalHealth,
  providerHealth,
}: OverviewPanelProps) {
  return (
    <section className="stack stack--large">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Overview</p>
          <h2>System snapshot</h2>
        </div>
        <p className="muted">A quick read on corpus health, runtime, and operator activity.</p>
      </div>

      <div className="grid grid--overview">
        <StatCard title="Documents" value={documentStats.total} note={`${documentStats.available} available`} />
        <StatCard title="Chunks" value={documentStats.indexedChunks} note={`${documentStats.duplicates} duplicates`} />
        <StatCard
          title="Runtime"
          value={runtimeStats ? formatDuration(runtimeStats.uptime_seconds) : 'unknown'}
          note={runtimeStats ? `since ${formatTimestamp(runtimeStats.started_at)}` : 'waiting for stats'}
        />
        <StatCard title="Queries" value={runtimeStats?.query_total ?? 0} note={`${runtimeStats?.audit_events_total ?? 0} audit events`} />
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
        <StatCard title="Provider" value={providerHealth?.status ?? 'unknown'} note={providerHealth?.model ?? 'not reported'} />
      </div>
    </section>
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
