import type { ChatTurn } from './workspace-model'

export function createId() {
  return globalThis.crypto?.randomUUID?.() ?? `item_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

export function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function formatDuration(seconds: number) {
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

export function safeDetailValue(value: unknown) {
  if (typeof value === 'string') {
    return value
  }

  try {
    return JSON.stringify(value)
  } catch {
    return 'unserializable'
  }
}

export function buildMemoryPrompt(question: string, turns: ChatTurn[]) {
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
