import type { FormEvent } from 'react'

import type { GuardrailCheckResponse, QueryResponse } from '../types'
import type { ChatTurn } from './workspace-model'
import { formatTimestamp } from './workspace-helpers'

interface ChatPanelProps {
  topK: number
  question: string
  guardrailPreview: GuardrailCheckResponse | null
  chatError: string | null
  querying: boolean
  displayedAnswer: string
  currentResponse: QueryResponse | null
  chatTurns: ChatTurn[]
  onAskQuestion: (event: FormEvent<HTMLFormElement>) => void
  onQuestionChange: (value: string) => void
  onTopKChange: (value: number) => void
}

export function ChatPanel({
  topK,
  question,
  guardrailPreview,
  chatError,
  querying,
  displayedAnswer,
  currentResponse,
  chatTurns,
  onAskQuestion,
  onQuestionChange,
  onTopKChange,
}: ChatPanelProps) {
  return (
    <section className="stack stack--large">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Grounded chat</p>
          <h2>Ask against the current corpus</h2>
        </div>
        <span className="pill pill--neutral">top_k {topK}</span>
      </div>

      <div className="grid grid--chat">
        <div className="panel">
          <form className="stack" onSubmit={onAskQuestion}>
            <label className="field">
              <span>Question</span>
              <textarea
                rows={6}
                value={question}
                onChange={(event) => onQuestionChange(event.target.value)}
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
                onChange={(event) => onTopKChange(Number(event.target.value))}
              />
            </label>

            <div className="upload-actions">
              <button type="submit" className="button button--primary" disabled={querying || !question.trim()}>
                {querying ? 'Thinking…' : 'Ask assistant'}
              </button>
              <span className="muted">Follow-up questions are sent with short session memory for continuity.</span>
            </div>

            {guardrailPreview && (
              <div className={guardrailPreview.allowed ? 'guardrail guardrail--ok' : 'guardrail guardrail--blocked'}>
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

        <div className="stack stack--large">
          <div className="panel">
            <div className="panel__header">
              <h3>Assistant answer</h3>
              {currentResponse && (
                <span className="pill pill--neutral">{Math.round(currentResponse.confidence * 100)}% confidence</span>
              )}
            </div>
            <div className="answer-box">{displayedAnswer || 'Your answer will appear here after a query.'}</div>
            {querying && <p className="muted answer-status">Streaming answer from the server…</p>}
            {currentResponse?.disclaimer && <p className="muted answer-disclaimer">{currentResponse.disclaimer}</p>}
          </div>

          <div className="panel">
            <div className="panel__header">
              <h3>Citations</h3>
              <span className="muted">{currentResponse?.citations.length ?? 0} sources</span>
            </div>
            <div className="stack stack--small">
              {currentResponse?.citations.map((citation) => (
                <details key={`${citation.chunk_id ?? citation.source}-${citation.source}`} className="citation-card">
                  <summary className="citation-card__summary">
                    <div className="citation-card__summary-title">
                      <strong>{citation.source}</strong>
                      <span className="muted">
                        {citation.page ? `Page ${citation.page}` : 'No page'} · {Math.round(citation.relevance_score * 100)}%
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
              {!currentResponse?.citations.length && <p className="muted">No citations yet.</p>}
            </div>
          </div>

          <div className="panel">
            <div className="panel__header">
              <h3>Session memory</h3>
              <span className="muted">{chatTurns.length} turns</span>
            </div>
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
      </div>
    </section>
  )
}
