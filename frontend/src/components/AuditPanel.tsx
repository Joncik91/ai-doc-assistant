import type { AuditEventRecord } from '../types'
import { formatTimestamp, safeDetailValue } from './workspace-helpers'

interface AuditPanelProps {
  auditFilter: string
  filteredAuditEvents: AuditEventRecord[]
  onAuditFilterChange: (value: string) => void
}

export function AuditPanel({ auditFilter, filteredAuditEvents, onAuditFilterChange }: AuditPanelProps) {
  return (
    <section className="stack stack--large">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Audit history</p>
          <h2>Server-side activity log</h2>
        </div>
        <span className="pill pill--neutral">{filteredAuditEvents.length} events</span>
      </div>

      <div className="panel stack stack--large">
        <label className="field">
          <span>Filter</span>
          <input
            value={auditFilter}
            onChange={(event) => onAuditFilterChange(event.target.value)}
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
              {Object.keys(event.details).length > 0 && <pre className="details-block">{safeDetailValue(event.details)}</pre>}
            </article>
          ))}
          {!filteredAuditEvents.length && <p className="muted">No matching events.</p>}
        </div>
      </div>
    </section>
  )
}
