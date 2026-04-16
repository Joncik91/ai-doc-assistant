import type { FormEvent } from 'react'

import type { DocumentRecord } from '../types'
import { formatBytes } from './workspace-helpers'

interface DocumentStats {
  total: number
}

interface DocumentsPanelProps {
  documentStats: DocumentStats
  selectedFiles: File[]
  uploading: boolean
  uploadProgress: number
  uploadError: string | null
  documents: DocumentRecord[]
  onUpload: (event: FormEvent<HTMLFormElement>) => void
  onFilesChange: (files: File[]) => void
  onDeleteDocument: (document: DocumentRecord) => void
}

export function DocumentsPanel({
  documentStats,
  selectedFiles,
  uploading,
  uploadProgress,
  uploadError,
  documents,
  onUpload,
  onFilesChange,
  onDeleteDocument,
}: DocumentsPanelProps) {
  return (
    <section className="stack stack--large">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Documents</p>
          <h2>Upload and curate source files</h2>
        </div>
        <span className="pill pill--neutral">{documentStats.total} total</span>
      </div>

      <div className="panel">
        <form className="upload-form" onSubmit={onUpload}>
          <label className="field">
            <span>Source files</span>
            <input
              type="file"
              accept=".txt,.md,.markdown,.pdf,.docx"
              multiple
              onChange={(event) => onFilesChange(Array.from(event.target.files ?? []))}
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
          <h3>Registry</h3>
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
                      onClick={() => void onDeleteDocument(document)}
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
  )
}
