import { useEffect, useState } from 'react'
import { AppShell, Sidebar, TopBar, SidebarItem } from '../components'
import { agent, HarnessQueryResponse, RuntimeHealth, system } from '../api/client'
import { colors } from '../styles'

type ChatMessage = {
  id: string
  role: 'user' | 'agent'
  text: string
  result?: HarnessQueryResponse
}

const initialMessage: ChatMessage = {
  id: 'welcome',
  role: 'agent',
  text: 'Я PO Agent. Могу найти задачу, показать evidence и выполнить доступный skill через Agent Core.',
}

function createSessionId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return `ui-${crypto.randomUUID()}`
  return `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function initialSessionId() {
  const key = 'po-agent-v3-session-id'
  const existing = window.sessionStorage.getItem(key)
  if (existing) return existing
  const created = createSessionId()
  window.sessionStorage.setItem(key, created)
  return created
}

function v3Meta(result?: HarnessQueryResponse) {
  const data = result?.data
  if (!data || typeof data !== 'object') return undefined
  const meta = data._agent_core_v3
  return meta && typeof meta === 'object' ? meta as Record<string, unknown> : undefined
}

export function AssistantView() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([initialMessage])
  const [currentSession, setCurrentSession] = useState(initialSessionId)
  const [health, setHealth] = useState<RuntimeHealth | null>(null)
  const [healthError, setHealthError] = useState(false)

  const refreshHealth = async () => {
    try {
      setHealth(await system.health())
      setHealthError(false)
    } catch {
      setHealth(null)
      setHealthError(true)
    }
  }

  useEffect(() => { void refreshHealth() }, [])

  const newConversation = () => {
    const next = createSessionId()
    window.sessionStorage.setItem('po-agent-v3-session-id', next)
    setCurrentSession(next)
    setMessages([initialMessage])
    setQuery('')
  }

  const handleQuery = async (override?: string) => {
    const text = (override ?? query).trim()
    if (!text || loading) return

    setMessages((items) => [...items, { id: `u-${Date.now()}`, role: 'user', text }])
    setQuery('')
    setLoading(true)

    try {
      const result = await agent.query({ query: text, session_id: currentSession })
      const answer = result.status === 'NEEDS_CLARIFICATION'
        ? result.question || 'Нужно уточнение.'
        : result.answer || 'Agent Core завершил запрос без текстового ответа.'
      setMessages((items) => [...items, {
        id: `a-${Date.now()}`,
        role: 'agent',
        text: answer,
        result,
      }])
    } catch {
      setMessages((items) => [...items, {
        id: `e-${Date.now()}`,
        role: 'agent',
        text: 'Не удалось обратиться к Agent API. Проверьте backend /api/v1/health.',
      }])
    } finally {
      setLoading(false)
    }
  }

  const runtimeLabel = healthError
    ? 'backend unavailable'
    : health?.agent_core_v3_enabled
      ? `Agent Core v3 · ${health.semantic_mode}`
      : health
        ? `Legacy Harness · ${health.semantic_mode}`
        : 'checking runtime…'

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
        </Sidebar>
      }
      content={
        <div style={{ flex: 1, minWidth: 0 }}>
          <TopBar title="Обзор" subtitle="PO Workspace · Agent Core" />
          <div style={{ maxWidth: 980, margin: '24px auto', padding: '0 24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 260px', gap: 16, marginBottom: 16 }}>
              <div style={{ background: '#fff', border: '1px solid #e7eaf0', borderRadius: 12, padding: 18 }}>
                <div style={{ fontSize: 12, color: '#667085', marginBottom: 6 }}>АГЕНТ</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: '#20242c' }}>Рабочий чат PO</div>
                <div style={{ fontSize: 13, color: '#667085', marginTop: 6 }}>LLM → Grounding → Contract → Capability → REAL AS21 → Evidence</div>
              </div>
              <div style={{ background: '#fff', border: '1px solid #e7eaf0', borderRadius: 12, padding: 18 }}>
                <div style={{ fontSize: 12, color: '#667085' }}>RUNTIME</div>
                <div style={{ fontSize: 12, fontWeight: 700, marginTop: 6, color: health?.agent_core_v3_enabled ? '#087443' : '#9a6700' }}>{runtimeLabel}</div>
                <div style={{ fontSize: 11, color: '#667085', marginTop: 10 }}>SESSION</div>
                <div style={{ fontSize: 11, fontWeight: 600, marginTop: 4, overflowWrap: 'anywhere' }}>{currentSession}</div>
                <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                  <button onClick={newConversation} disabled={loading} style={{ border: '1px solid #d9dee8', background: '#fff', borderRadius: 8, padding: '6px 9px', cursor: 'pointer', fontSize: 11 }}>Новый диалог</button>
                  <button onClick={() => void refreshHealth()} style={{ border: '1px solid #d9dee8', background: '#fff', borderRadius: 8, padding: '6px 9px', cursor: 'pointer', fontSize: 11 }}>Проверить</button>
                </div>
              </div>
            </div>

            <div style={{ background: '#fff', border: '1px solid #e7eaf0', borderRadius: 12, minHeight: 520, display: 'flex', flexDirection: 'column' }}>
              <div style={{ flex: 1, padding: 20, display: 'flex', flexDirection: 'column', gap: 14 }}>
                {messages.map((message) => {
                  const meta = v3Meta(message.result)
                  const routedV3 = Boolean(meta)
                  return (
                    <div key={message.id} style={{ alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '78%' }}>
                      <div style={{
                        padding: '12px 14px', borderRadius: 12,
                        background: message.role === 'user' ? colors.accentPrimary : '#f5f7fa',
                        color: message.role === 'user' ? '#fff' : '#20242c', fontSize: 14, lineHeight: 1.5,
                      }}>{message.text}</div>
                      {message.result && (
                        <div style={{ marginTop: 7, fontSize: 11, color: '#667085' }}>
                          {message.result.skill && <span>{message.result.skill.id}@{message.result.skill.version} · </span>}
                          <span>{message.result.status} · {message.result.latency_ms} ms · evidence {message.result.evidence.length}</span>
                          <span> · {routedV3 ? `v3/${String(meta?.stage || '?')}` : 'legacy'}</span>
                          {meta?.llm_used === true && <span> · LLM</span>}
                        </div>
                      )}
                      {message.result?.status === 'NEEDS_CLARIFICATION' && message.result.options.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8 }}>
                          {message.result.options.map((option) => (
                            <button key={option} onClick={() => handleQuery(option)} style={{ border: '1px solid #d9dee8', background: '#fff', borderRadius: 14, padding: '6px 10px', cursor: 'pointer', fontSize: 12 }}>{option}</button>
                          ))}
                        </div>
                      )}
                    </div>
                  )
                })}
                {loading && <div style={{ color: '#667085', fontSize: 13 }}>Agent Core выполняет запрос…</div>}
              </div>

              <div style={{ borderTop: '1px solid #e7eaf0', padding: 16, display: 'flex', gap: 10 }}>
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  onKeyDown={(event) => event.key === 'Enter' && handleQuery()}
                  placeholder="Например: Задачи Калачанова в WMB"
                  style={{ flex: 1, border: '1px solid #d9dee8', borderRadius: 9, padding: '12px 14px', fontSize: 14, outline: 'none' }}
                />
                <button onClick={() => handleQuery()} disabled={loading || !query.trim()} style={{ border: 0, borderRadius: 9, padding: '0 20px', background: colors.accentPrimary, color: '#fff', fontWeight: 600, cursor: loading ? 'wait' : 'pointer', opacity: loading || !query.trim() ? .55 : 1 }}>
                  Отправить
                </button>
              </div>
            </div>
          </div>
        </div>
      }
    />
  )
}

export default AssistantView
