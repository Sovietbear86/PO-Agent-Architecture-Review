import { useState, useEffect } from 'react'
import { AppShell, Sidebar, Branding, TopBar, SidebarItem, FilterBar, TaskCard, TaskList, EmptyState, AgentButton, AgentChat } from '../components'
import { colors } from '../styles'

export function AssistantView() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState<string>('Ask me about tasks, sprints, team, or quality!')
  const [loading, setLoading] = useState(false)
  const [history, setHistory] = useState<{ query: string; answer: string }[]>([])
  const [isAgentOpen, setIsAgentOpen] = useState(false)

  const handleQuery = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await fetch('/api/v1/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      const data = await res.json()
      setResponse(data.response)
      setHistory((prev) => [...prev, { query, answer: data.response }])
      setQuery('')
    } catch (error) {
      setResponse('Error: Could not process query')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppShell
      sidebar={
        <Sidebar>
          <SidebarItem label="Обзор" active />
          <SidebarItem label="Задачи" onClick={() => window.location.href = '/tasks'} />
          <SidebarItem label="Спринты" onClick={() => window.location.href = '/sprint'} />
          <SidebarItem label="Релизы" onClick={() => window.location.href = '/releases'} />
          <SidebarItem label="Команда" onClick={() => window.location.href = '/team'} />
          <SidebarItem label="Аналитика" onClick={() => window.location.href = '/quality'} />
          <SidebarItem label="История" onClick={() => window.location.href = '/history'} />
        </Sidebar>
      }
      content={
        <div style={{ flex: 1 }}>
          <TopBar
            title="Ассистент"
            subtitle="Интеллектуальный помощник PO"
            rightContent={
              <AgentButton onClick={() => setIsAgentOpen(true)} />
            }
          />

          <div style={{
            maxWidth: '800px',
            margin: '0 auto',
            marginTop: '2rem',
            backgroundColor: '#ffffff',
            borderRadius: '8px',
            boxShadow: '0 1px 3px rgba(27, 39, 61, 0.08)',
            padding: '24px',
          }}>
            <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#20242c', margin: '0 0 24px' }}>
              Чат с агентом
            </h2>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
                placeholder="Задайте вопрос агенту..."
                style={{
                  flex: 1,
                  padding: '12px 16px',
                  border: '1px solid #d9dee8',
                  borderRadius: '8px',
                  fontSize: '14px',
                  outline: 'none',
                }}
              />
              <button
                onClick={handleQuery}
                disabled={loading}
                style={{
                  padding: '12px 24px',
                  backgroundColor: loading ? colors.borderSoft : colors.accentPrimary,
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight: 600,
                }}
              >
                {loading ? '...' : 'Отправить'}
              </button>
            </div>

            <div style={{
              backgroundColor: '#f5f7fa',
              borderRadius: '8px',
              padding: '16px',
              minHeight: '150px',
            }}>
              <p style={{ fontSize: '14px', color: '#667085' }}>
                <strong>Агент:</strong> {response}
              </p>
            </div>

            {history.length > 0 && (
              <div style={{ marginTop: '24px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#20242c', marginBottom: '16px' }}>
                  История
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {history.map((item, i) => (
                    <div key={i} style={{
                      padding: '16px',
                      backgroundColor: '#ffffff',
                      borderRadius: '8px',
                      boxShadow: '0 1px 3px rgba(27, 39, 61, 0.08)',
                    }}>
                      <p style={{ fontSize: '13px', fontWeight: 600, color: '#20242c', marginBottom: '8px' }}>
                        Вы: {item.query}
                      </p>
                      <p style={{ fontSize: '14px', color: '#667085' }}>
                        Агент: {item.answer}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      }
    />
  )
}

export default AssistantView
