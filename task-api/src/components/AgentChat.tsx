import { useState, useRef, useEffect } from 'react'
import { colors } from '../styles'

interface AgentMessage {
  id: string
  role: 'user' | 'agent' | 'system'
  content: string
  timestamp: string
  taskData?: Array<{
    id: string
    source_id: string
    title: string
    status: string
    assignee?: string
    description?: string
    source_url?: string
  }>
}

interface AgentChatProps {
  isOpen: boolean
  onClose: () => void
}

export function AgentChat({ isOpen, onClose }: AgentChatProps) {
  const [query, setQuery] = useState('')
  const [isExecuting, setIsExecuting] = useState(false)
  const [messages, setMessages] = useState<AgentMessage[]>([
    {
      id: 'welcome',
      role: 'agent',
      content: `Я - ассистент продукт-овладельца для анализа команды в SberWorks Task Tracker (SWTR).

### Доступные скиллы:
1. **Здоровье спринта** - метрики спринта: Committed scope, Completed scope, Throughput
   Пример: 'здоровье спринта OLP-SPRNT-3'

2. **Velocity** - скорость команды за период
   Пример: 'скорость команды' или 'velocity за последние 6 спринтов'

3. **Flow metrics** - метрики потока: Throughput, Cycle time, Lead time
   Пример: 'поток задач за 30 дней'

4. **Баланс загрузки** - распределение задач между сотрудниками
   Пример: 'баланс загрузки команды'

5. **Узкие места** - анализ бутылочных горлышек в процессе
   Пример: 'бутылочное горлышко в спринте'

6. **Прогноз** - прогноз завершения спринта
   Пример: 'прогноз завершения спринта'

7. **Компетенции** - подбор сотрудников по компетенциям
   Пример: 'кто подходит для задачи'

8. **Релизы** - задачи, привязанные к релизу
   Пример: 'релизные задачи OLAP'

Также я могу показать задачи по участнику или спринту.
Просто спросите: 'задачи Гаранина в спринте OLP-SPRNT-3'`,
      timestamp: new Date().toLocaleTimeString('ru-RU'),
    },
  ])
  const [currentTasks, setCurrentTasks] = useState<AgentMessage[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll messages to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = async () => {
    if (!query.trim()) return

    const userMessage: AgentMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query.trim(),
      timestamp: new Date().toLocaleTimeString('ru-RU'),
    }

    // Clear previous tasks
    setCurrentTasks([])

    setMessages(prev => [...prev, userMessage])
    setQuery('')
    setIsExecuting(true)

    try {
      // Send to MCP server endpoint (TeamPerformanceAgent handles all queries)
      const history = messages.map(m => ({
        role: m.role === 'system' ? 'assistant' : m.role,
        content: m.content,
      })).slice(-10) as Array<{role: string, content: string}>

      const response = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userMessage.content,
          history: history
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()

      // Add agent response
      const agentMessage: AgentMessage = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: data.response || JSON.stringify(data) || 'Я получила ответ от системы',
        timestamp: new Date().toLocaleTimeString('ru-RU'),
      }

      setMessages(prev => [...prev, agentMessage])

      // If it's a search, show tasks
      if (data.tasks && data.tasks.length > 0) {
        setCurrentTasks(prev => [...prev, {
          id: 'search-' + Date.now(),
          role: 'agent',
          content: `Найдено ${data.tasks.length} задач по вашему запросу`,
          timestamp: new Date().toLocaleTimeString('ru-RU'),
          taskData: data.tasks.map((t: any) => ({
            id: t.id || t.source_id,
            source_id: t.source_id,
            title: t.title,
            status: t.status,
            assignee: t.assignee,
            description: t.description,
            source_url: t.source_url || t.url,
          })),
        }])
      }
      
      // If it's team performance analysis, show findings (only if no tasks)
      // For task searches, findings are already in data.tasks
      if (data.findings && data.findings.length > 0 && (!data.tasks || data.tasks.length === 0)) {
        setCurrentTasks(prev => [...prev, {
          id: 'team-analysis-' + Date.now(),
          role: 'agent',
          content: `Анализ команды: ${data.status || 'анализ'}`,
          timestamp: new Date().toLocaleTimeString('ru-RU'),
          findings: data.findings,
          risks: data.risks || [],
          recommendations: data.recommendations || [],
        }])
      }

      // If it's a summarize, trigger task details fetch
      if (data.task_id) {
        setCurrentTasks(prev => [...prev, {
          id: (Date.now() + 2).toString(),
          role: 'system',
          content: `Загружаю детали задачи ${data.task_id}...`,
          timestamp: new Date().toLocaleTimeString('ru-RU'),
        }])

        // Call summarize endpoint
        try {
          const summaryResponse = await fetch('/tasks/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: data.task_id }),
          })

          if (summaryResponse.ok) {
            const summaryData = await summaryResponse.json()
            setCurrentTasks(prev => [...prev, {
              id: (Date.now() + 3).toString(),
              role: 'agent',
              content: summaryData.summary,
              timestamp: new Date().toLocaleTimeString('ru-RU'),
              taskData: summaryData.task ? [{
                id: summaryData.task.id || summaryData.task.source_id,
                source_id: summaryData.task.source_id,
                title: summaryData.task.title,
                status: summaryData.task.status,
                assignee: summaryData.task.assignee,
                description: summaryData.task.description,
                source_url: summaryData.task.source_url || summaryData.task.url,
              }] : [],
            }])
          } else {
            const errorData = await summaryResponse.json()
            setCurrentTasks(prev => [...prev, {
              id: (Date.now() + 3).toString(),
              role: 'system',
              content: `Ошибка при суммаризации: ${errorData.detail || 'Неизвестная ошибка'}`,
              timestamp: new Date().toLocaleTimeString('ru-RU'),
            }])
          }
        } catch (error) {
          setCurrentTasks(prev => [...prev, {
            id: (Date.now() + 3).toString(),
            role: 'system',
            content: `Ошибка при суммаризации: ${(error as Error).message}`,
            timestamp: new Date().toLocaleTimeString('ru-RU'),
          }])
        }
      }
    } catch (error) {
      const errorMessage: AgentMessage = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `Ошибка: ${(error as Error).message}. Проверьте запуск MCP-сервера на порту 3001`,
        timestamp: new Date().toLocaleTimeString('ru-RU'),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsExecuting(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isExecuting) {
      sendMessage()
    }
  }

  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '18rem',
        right: '2rem',
        width: '450px',
        maxHeight: '70vh',
        backgroundColor: '#fff',
        borderRadius: '16px',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        zIndex: 9998,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '1px solid #e5e7eb',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '1rem 1.25rem',
          backgroundColor: colors.accentPrimary,
          color: '#fff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '6px',
              backgroundColor: 'rgba(255, 255, 255, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <rect x="8" y="10" width="32" height="28" rx="8" fill="white" stroke="rgba(255,255,255,0.3)" strokeWidth="2" />
              <circle cx="18" cy="20" r="3" fill="#315fa8" />
              <circle cx="30" cy="20" r="3" fill="#315fa8" />
              <path d="M18 28C18 28 20 30 24 30C28 30 30 28 30 28" stroke="#315fa8" strokeWidth="2" strokeLinecap="round" />
              <line x1="24" y1="10" x2="24" y2="4" stroke="#315fa8" strokeWidth="2" />
              <circle cx="24" cy="4" r="2" fill="#315fa8" />
            </svg>
          </div>
          <span
            style={{
              fontWeight: 600,
              fontSize: '0.95rem',
            }}
          >
            Агент продукта
          </span>
        </div>

        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '1.5rem',
            cursor: 'pointer',
            color: 'rgba(255, 255, 255, 0.8)',
            padding: '0.25rem',
            lineHeight: 1,
            transition: 'color 0.2s',
          }}
          onMouseOver={(e) => (e.currentTarget.style.color = '#fff')}
          onMouseOut={(e) => (e.currentTarget.style.color = 'rgba(255, 255, 255, 0.8)')}
        >
          ×
        </button>
      </div>

      {/* Chat Area */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '1rem',
          backgroundColor: '#f9fafb',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              alignItems: msg.role === 'agent' ? 'flex-start' : 'flex-end',
            }}
          >
            {/* Avatar */}
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: msg.role === 'user' ? '#10b981' : colors.accentPrimary,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                margin: msg.role === 'user' ? '0 0 0 0.75rem' : '0 0.75rem 0 0',
              }}
            >
              {msg.role === 'user' ? (
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              ) : (
                <svg width="18" height="18" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="8" y="10" width="32" height="28" rx="8" fill="white" stroke="rgba(255,255,255,0.3)" strokeWidth="2" />
                  <circle cx="18" cy="20" r="3" fill="#315fa8" />
                  <circle cx="30" cy="20" r="3" fill="#315fa8" />
                  <path d="M18 28C18 28 20 30 24 30C28 30 30 28 30 28" stroke="#315fa8" strokeWidth="2" strokeLinecap="round" />
                  <line x1="24" y1="10" x2="24" y2="4" stroke="#315fa8" strokeWidth="2" />
                  <circle cx="24" cy="4" r="2" fill="#315fa8" />
                </svg>
              )}
            </div>

            {/* Message Bubble */}
            <div
              style={{
                maxWidth: '75%',
                padding: '0.75rem 1rem',
                borderRadius: '18px',
                fontSize: '0.9rem',
                lineHeight: 1.5,
                backgroundColor: msg.role === 'user' ? colors.accentPrimary : '#fff',
                color: msg.role === 'user' ? '#fff' : '#1f2937',
                boxShadow: msg.role === 'user' ? 'none' : '0 1px 2px rgba(0, 0, 0, 0.05)',
              }}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Task cards (for search results) */}
        {currentTasks.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {currentTasks.map((msg, idx) => (
              <div key={idx} style={{ backgroundColor: '#fff', borderRadius: '12px', padding: '1rem', boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)' }}>
                {msg.content}
                
                {/* Regular task data */}
                {msg.taskData && msg.taskData.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
                    {msg.taskData.map((task) => (
                      <div key={task.source_id} style={{ padding: '0.75rem', backgroundColor: '#f9fafb', borderRadius: '8px', border: '1px solid #e5e7eb' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                          {task.source_url ? (
                            <a
                              href={task.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ fontFamily: 'monospace', fontSize: '0.8rem', backgroundColor: '#e5e7eb', padding: '0.15rem 0.5rem', borderRadius: '4px', textDecoration: 'none', color: colors.accentPrimary }}
                            >
                              {task.source_id}
                            </a>
                          ) : (
                            <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', backgroundColor: '#e5e7eb', padding: '0.15rem 0.5rem', borderRadius: '4px' }}>
                              {task.source_id}
                            </span>
                          )}
                          <span
                            style={{
                              padding: '0.15rem 0.5rem',
                              fontSize: '0.75rem',
                              fontWeight: 500,
                              backgroundColor: task.status === 'done' ? '#dcfce7' : task.status === 'in_progress' ? '#fef3c7' : '#fee2e2',
                              color: task.status === 'done' ? '#166534' : task.status === 'in_progress' ? '#92400e' : '#991b1b',
                              borderRadius: '4px',
                            }}
                          >
                            {task.status}
                          </span>
                        </div>
                        <div style={{ fontWeight: 500, fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                          {task.title}
                        </div>
                        {task.assignee && <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>Исполнитель: {task.assignee}</div>}
                        {task.source_url && (
                          <a
                            href={task.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{
                              fontSize: '0.8rem',
                              color: colors.accentPrimary,
                              textDecoration: 'none',
                              marginTop: '0.5rem',
                              display: 'inline-block',
                            }}
                          >
                            👉 Открыть в SWTR
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Team performance analysis findings */}
                {msg.findings && msg.findings.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.75rem' }}>
                    {msg.findings.map((finding, fIdx) => (
                      <div key={fIdx} style={{ padding: '0.5rem', backgroundColor: '#f0f9ff', borderRadius: '8px', borderLeft: '3px solid #3b82f6' }}>
                        {finding}
                      </div>
                    ))}
                    
                    {msg.risks && msg.risks.length > 0 && (
                      <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: 'fff1f2', borderRadius: '8px', borderLeft: '3px solid #ef4444' }}>
                        <strong>Риски:</strong>
                        <ul style={{ margin: '0.5rem 0 0 1.5rem', padding: 0 }}>
                          {msg.risks.map((risk, rIdx) => (
                            <li key={rIdx}>{risk}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {msg.recommendations && msg.recommendations.length > 0 && (
                      <div style={{ marginTop: '0.5rem', padding: '0.5rem', backgroundColor: 'f0fdf4', borderRadius: '8px', borderLeft: '3px solid #22c55e' }}>
                        <strong>Рекомендации:</strong>
                        <ul style={{ margin: '0.5rem 0 0 1.5rem', padding: 0 }}>
                          {msg.recommendations.map((rec, rIdx) => (
                            <li key={rIdx}>{rec}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ padding: '1rem', borderTop: '1px solid #e5e7eb', backgroundColor: '#fff' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Задайте вопрос агенту..."
            disabled={isExecuting}
            style={{
              flex: 1,
              padding: '0.75rem 1rem',
              borderRadius: '24px',
              border: '1px solid #d1d5db',
              fontSize: '0.9rem',
              outline: 'none',
            }}
          />
          <button
            onClick={sendMessage}
            disabled={isExecuting || !query.trim()}
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '50%',
              backgroundColor: isExecuting || !query.trim() ? '#9ca3af' : colors.accentPrimary,
              color: '#fff',
              border: 'none',
              cursor: isExecuting ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'background-color 0.2s',
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M22 2L11 13" />
              <path d="M22 2L15 22L11 13L2 9L22 2Z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
