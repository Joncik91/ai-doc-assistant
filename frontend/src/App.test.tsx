import { describe, expect, it, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import App from './App'

describe('App', () => {
  it('renders config information from the backend endpoint', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          app_name: 'AI Document Assistant',
          version: '0.1.0',
          llm_provider: 'deepseek',
          llm_model: 'deepseek-chat',
        }),
      }),
    )

    render(<App />)

    await waitFor(() => {
      expect(
        screen.getByRole('heading', { name: /AI Document Assistant/i }),
      ).toBeInTheDocument()
      expect(screen.getByText(/LLM Provider:/i)).toBeInTheDocument()
      expect(screen.getByText(/deepseek-chat/i)).toBeInTheDocument()
    })
  })
})
