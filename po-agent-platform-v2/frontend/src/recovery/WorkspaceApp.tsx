import { FormEvent, useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { agent, HarnessQueryResponse, RuntimeHealth, system } from '../api/client'
import './workspace.css'

type Message = {
  id: string
  role: 'user' | 'agent'
  text: string
  result?: HarnessQueryResponse
  feedback?: 'up' | 'down'
}

const nav = [
  ['/', 'Обзор', '▦'],
  ['/tasks', 'Задачи', '✓'],
  ['/sprint', 'Спринты', '◷'],
  ['/releases', 'Релизы', '◇'],
  ['/team', 'Команда', '♙'],
  ['/quality', 'Качество', '◎'],
] as const

const SESSION_KEY = 'po-agent-runtime-session-id'

function createSessionId(): string {
  return `ui-${crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(16).slice(2)}`}`
}

function getTabSessionId(): string {
  const current = window.sessionStorage.getItem(SESSION_KEY)
  if (current) return current
  const created = createSessionId()
  window.sessionStorage.setItem(SESSION_KEY, created)
  return created
}

function resetTabSessionId(): string {
  const created = createSessionId()
  window.sessionStorage.setItem(SESSION_KEY, created)
  return created
}

function v3Meta(result?: HarnessQueryResponse): Record<string, unknown> | null {
  const data = result?.data
  if (!data || typeof data !== 'object') return null
  const candidate = data['_agent_core_v3']
  return candidate && typeof candidate === 'object' ? candidate as Record<string, unknown> : null
}

function runtimeLabel(health: RuntimeHealth | null, result?: HarnessQueryResponse): string {
  const meta = v3Meta(result)
  if (meta) return `Agent Core v3${meta.stage ? `/${String(meta.stage)}` : ''}`
  if (health?.agent_core_v3_enabled) return 'Agent Core v3 · ready'
  return 'Legacy Harness'
}

function Evidence({ result }: { result: HarnessQueryResponse }) {
  const [open, setOpen] = useState(false)
  const meta = v3Meta(result)
  const hasDetails = result.evidence.length > 0 || result.warnings.length > 0 || Boolean(meta)
  if (!hasDetails) return null
  return (
    <div className="chat-evidence">
      <button className="link-button" onClick={() => setOpen(v => !v)}>
        {open ? 'Скрыть детали' : `Evidence ${result.evidence.length} · trace`}
      </button>
      {open && (
        <div className="evidence-panel">
          <div className="trace">trace_id: {result.trace_id}</div>
          <div className="trace">session_id: {result.session_id}</div>
          {result.skill && <div className="trace">skill: {result.skill.id}@{result.skill.version}</div>}
          {meta && <div className="trace">runtime: Agent Core v3 · stage={String(meta.stage ?? 'unknown')} · llm_used={String(meta.llm_used ?? 'unknown')}</div>}
          {result.warnings.map(w => <div key={w} className="warning">⚠ {w}</div>)}
          {result.evidence.slice(0, 12).map((item, idx) => (
            <div className="evidence-row" key={`${item.entity_id ?? item.label}-${idx}`}>
              <span>{item.source}</span><b>{item.entity_id ?? item.label}</b><span>{String(item.value ?? '')}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function AgentChat({ open, onClose }: { open: boolean; onClose(): void }) {
  const [sessionId, setSessionId] = useState(getTabSessionId)
  const [health, setHealth] = useState<RuntimeHealth | null>(null)
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<Message[]>([{
    id: 'hello', role: 'agent', text: 'Я PO Agent. Новый диалог изолирован от предыдущих turn/correction states. Факты проверяю по authoritative source.'
  }])

  useEffect(() => {
    let cancelled = false
    system.health()
      .then(value => { if (!cancelled) setHealth(value) })
      .catch(() => { if (!cancelled) setHealth(null) })
    return () => { cancelled = true }
  }, [])

  function newConversation() {
    const fresh = resetTabSessionId()
    setSessionId(fresh)
    setInput('')
    setMessages([{
      id: `hello-${fresh}`,
      role: 'agent',
      text: 'Новый диалог создан. Предыдущий transient dialogue state не используется.'
    }])
  }

  async function send(textOverride?: string) {
    const text = (textOverride ?? input).trim()
    if (!text || busy) return
    setMessages(items => [...items, { id: crypto.randomUUID(), role: 'user', text }])
    setInput('')
    setBusy(true)
    try {
      const result = await agent.query({ query: text, session_id: sessionId })
      const textResult = result.status === 'NEEDS_CLARIFICATION'
        ? result.question ?? 'Нужно уточнение.'
        : result.answer ?? 'Запрос выполнен.'
      setMessages(items => [...items, { id: crypto.randomUUID(), role: 'agent', text: textResult, result }])
    } catch {
      setMessages(items => [...items, { id: crypto.randomUUID(), role: 'agent', text: 'Agent Core API недоступен. Проверьте backend /api/v1/health.' }])
    } finally {
      setBusy(false)
    }
  }

  async function submitFeedback(messageId: string, result: HarnessQueryResponse, rating: 'up' | 'down') {
    try {
      await agent.feedback(result.trace_id, {
        rating,
        comment: rating === 'down' ? 'User requested improvement from PO Agent chat' : 'User confirmed answer',
      })
      setMessages(items => items.map(item => item.id === messageId ? { ...item, feedback: rating } : item))
      if (rating === 'down') {
        setMessages(items => [...items, {
          id: crypto.randomUUID(), role: 'agent',
          text: 'Обратная связь сохранена. Learning Reviewer должен перепроверить источник и локализовать причину; если доказательств недостаточно, я попрошу только конкретное уточнение.'
        }])
      }
    } catch {
      setMessages(items => [...items, { id: crypto.randomUUID(), role: 'agent', text: 'Не удалось сохранить обратную связь.' }])
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    void send()
  }

  const latestResult = [...messages].reverse().find(message => message.result)?.result
  const label = runtimeLabel(health, latestResult)

  return (
    <aside className={`agent-drawer ${open ? 'agent-drawer-open' : ''}`} aria-hidden={!open}>
      <header className="agent-header">
        <div>
          <div className="agent-kicker">PO AGENT</div>
          <strong>Помощник владельца продукта</strong>
          <div className="trace" style={{ marginTop: 6 }}>{label}</div>
          <div className="trace" style={{ marginTop: 2, maxWidth: 330, overflowWrap: 'anywhere' }}>session: {sessionId}</div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
          <button className="link-button" onClick={newConversation} disabled={busy}>Новый диалог</button>
          <button className="icon-button" onClick={onClose} aria-label="Закрыть">×</button>
        </div>
      </header>
      <div className="chat-stream">
        {messages.map(message => (
          <div className={`message ${message.role}`} key={message.id}>
            <div className="bubble">{message.text}</div>
            {message.result && (
              <div className="trace" style={{ marginTop: 6 }}>
                {runtimeLabel(health, message.result)} · {message.result.status} · {Math.round(message.result.latency_ms)} ms
              </div>
            )}
            {message.result && <Evidence result={message.result} />}
            {message.result?.status === 'NEEDS_CLARIFICATION' && message.result.options.length > 0 && (
              <div className="option-row">
                {message.result.options.map(option => (
                  <button key={option} onClick={() => void send(option)}>{option}</button>
                ))}
              </div>
            )}
            {message.role === 'agent' && message.result && ['COMPLETED', 'PARTIAL'].includes(message.result.status) && (
              <div className="feedback-row">
                {message.feedback ? (
                  <span>{message.feedback === 'up' ? 'Ответ принят' : 'ОС сохранена'}</span>
                ) : (
                  <>
                    <span>Ответ помог?</span>
                    <button onClick={() => void submitFeedback(message.id, message.result!, 'up')}>Да</button>
                    <button onClick={() => void submitFeedback(message.id, message.result!, 'down')}>Нет / улучшить</button>
                  </>
                )}
              </div>
            )}
          </div>
        ))}
        {busy && <div className="typing">Agent Core анализирует запрос и проверяет source facts…</div>}
      </div>
      <form className="chat-compose" onSubmit={submit}>
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              void send()
            }
          }}
          placeholder="Спросите естественным языком…"
          rows={3}
        />
        <button type="submit" disabled={!input.trim() || busy}>Отправить</button>
      </form>
    </aside>
  )
}

export function WorkspaceApp() {
  const [agentOpen, setAgentOpen] = useState(false)
  return (
    <div className="workspace">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="works-logo">WORKS</div>
          <div className="brand-title">PO Space</div>
          <div className="brand-subtitle">DB Tribe</div>
        </div>
        <nav>
          {nav.map(([to, label, icon]) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
              <span className="nav-icon">{icon}</span><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="status-dot" /> Agent Core entry
        </div>
      </aside>
      <main className="main-area">
        <header className="topbar">
          <div><strong>Пространство владельца продукта</strong><span>Platform V · DB</span></div>
          <div className="topbar-actions"><button>OLP</button><button>DataMarts</button><button>DTMS</button></div>
        </header>
        <Outlet context={{ openAgent: () => setAgentOpen(true) }} />
      </main>
      <button className="agent-launcher" onClick={() => setAgentOpen(true)} aria-label="Открыть PO Agent">AI</button>
      <div className={`drawer-scrim ${agentOpen ? 'visible' : ''}`} onClick={() => setAgentOpen(false)} />
      <AgentChat open={agentOpen} onClose={() => setAgentOpen(false)} />
    </div>
  )
}
