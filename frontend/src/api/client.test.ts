import { describe, expect, it, vi, afterEach } from 'vitest'

import { streamQueryDocuments } from './client'
import type { AuthSession } from '../types'

const session: AuthSession = {
  kind: 'api_key',
  token: 'test-api-key',
  username: 'admin',
  scopes: ['read'],
}

function makeStreamResponse(chunks: string[]) {
  const encoder = new TextEncoder()
  return new Response(
    new ReadableStream({
      start(controller) {
        for (const chunk of chunks) {
          controller.enqueue(encoder.encode(chunk))
        }
        controller.close()
      },
    }),
    {
      status: 200,
      headers: { 'Content-Type': 'application/x-ndjson' },
    },
  )
}

describe('streamQueryDocuments', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns the final response and forwards streamed deltas', async () => {
    const onDelta = vi.fn()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        makeStreamResponse([
          '{"type":"delta","delta":"Hello "}\n',
          '{"type":"delta","delta":"world"}\n',
          '{"type":"final","response":{"answer":"Hello world","citations":[],"confidence":0.8,"finish_reason":"stop","disclaimer":null}}\n',
        ]),
      ),
    )

    const response = await streamQueryDocuments(session, 'Hello?', 3, onDelta)

    expect(onDelta).toHaveBeenNthCalledWith(1, 'Hello ')
    expect(onDelta).toHaveBeenNthCalledWith(2, 'world')
    expect(response.answer).toBe('Hello world')
    expect(response.finish_reason).toBe('stop')
  })

  it('raises a user-friendly error for malformed streaming payloads', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        makeStreamResponse([
          '{"type":"delta","delta":"Hello"}\n',
          '{"type":"final","response":',
        ]),
      ),
    )

    await expect(streamQueryDocuments(session, 'Hello?', 3)).rejects.toThrow(
      /Invalid streaming response:/,
    )
  })
})
