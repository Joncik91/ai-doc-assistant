import type { Citation } from '../types'

export type Panel = 'overview' | 'documents' | 'chat' | 'audit'
export type LoginMode = 'password' | 'api-key'
export type ThemeMode = 'dark' | 'light'

export interface ChatTurn {
  id: string
  question: string
  answer: string
  citations: Citation[]
  confidence: number
  disclaimer: string | null
  createdAt: string
}

export const panelLabels: Record<Panel, string> = {
  overview: 'Overview',
  documents: 'Documents',
  chat: 'Chat',
  audit: 'Audit',
}
