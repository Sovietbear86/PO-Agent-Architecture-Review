import { FormEvent, useMemo, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { agent, HarnessQueryResponse } from '../api/client'
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

function getSessionId(): string {
  const key = 'po-agent-session-id'
  const current = localStorage.getItem(key)
  if (current) return current
  const created = `po-${crypto.randomUUID?.() ?? Date.now()}`
  localStorage.setItem(key, created)
  return created
}

function Evidence({ result }: { result: HarnessQueryResponse }) {
  const [open, setOpen] = useState(false)
  if (!result.evidence.length && !result.warnings.length) return null
  return (
    <div className="chat-evidence">
      <button className="link-button" onClick={() => setOpen(v => !v)}>
        {open ? 'Скрыть детали' : `Evidence ${result.evidence.length} · trace`}
      </button>
      {open && (
        <div className="evidence-panel">
          <div className="trace">trace_id: {result.trace_id}</div>
          {result.skill && <div className="trace">skill: {result.skill.id}@{result.skill.version}</div>}
          {result.warnings.map(w => <div key={w} className="warning">⚠ {w}</div>)}
          {result.evidence.slice(0, 8).map((item, idx) => (
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
  const sessionId = useMemo(getSessionId, [])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<Message[]>([{
    id: 'hello', role: 'agent', text: 'Я PO Agent. Если запрос неоднозначен — уточню, а не буду угадывать. Ответы строю через Skills и evidence.'
  }])

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
      setMessages(items => [...items, { id: crypto.randomUUID(), role: 'agent', text: 'Harness API недоступен. Проверьте backend.' }])
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
          text: 'Что именно было неверно или чего не хватило? Напишите исправление — я сохраню его как feedback/eval-кандидат, а повторяющееся правило смогу запомнить в конфигурации.'
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

  return (
    <aside className={`agent-drawer ${open ? 'agent-drawer-open' : ''}`} aria-hidden={!open}>
      <header className="agent-header">
        <div><div className="agent-kicker">PO AGENT</div><strong>Помощник владельца продукта</strong></div>
        <button className="icon-button" onClick={onClose} aria-label="Закрыть">×</button>
      </header>
      <div className="chat-stream">
        {messages.map(message => (
          <div className={`message ${message.role}`} key={message.id}>
            <div className="bubble">{message.text}</div>
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
                  <span>{message.feedback === 'up' ? 'Ответ принят' : 'ОС сохранена · уточните, что улучшить'}</span>
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
        {busy && <div className="typing">Harness анализирует запрос и проверяет source facts…</div>}
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
          placeholder="Спросите естественным языком — агент уточнит неоднозначности…"
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
          <span className="status-dot" /> Harness Dialogue
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
