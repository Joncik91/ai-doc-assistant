import { useState, useEffect } from 'react'

interface ConfigInfo {
  app_name: string
  version: string
  llm_provider: string
  llm_model: string
}

function App() {
  const [config, setConfig] = useState<ConfigInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await fetch('/api/v1/config')
        if (!response.ok) {
          throw new Error('Failed to fetch config')
        }
        const data = await response.json()
        setConfig(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchConfig()
  }, [])

  return (
    <div style={{ padding: '20px' }}>
      <h1>AI Document Assistant</h1>
      {loading && <p>Loading configuration...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {config && (
        <div>
          <p><strong>App:</strong> {config.app_name} v{config.version}</p>
          <p><strong>LLM Provider:</strong> {config.llm_provider}</p>
          <p><strong>Model:</strong> {config.llm_model}</p>
        </div>
      )}
    </div>
  )
}

export default App
