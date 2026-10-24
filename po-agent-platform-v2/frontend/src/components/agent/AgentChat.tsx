import React, { useEffect, useRef } from 'react'
import { colors, spacing, radius, shadows } from '../../styles'

interface AgentChatProps {
  isOpen: boolean
  onClose: () => void
}

export function AgentChat({ isOpen, onClose }: AgentChatProps) {
  const [messages, setMessages] = React.useState<{role: 'user' | 'assistant', content: string}[]>([])
  const [input, setInput] = React.useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage = input
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setInput('')

    // Simulate agent response
    setTimeout(() => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Это демо-ответ агента. В реальном приложении здесь будет результат запроса к PO Agent v2.1.'
      }])
    }, 500)
  }

  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '600px',
        maxWidth: '90vw',
        maxHeight: '80vh',
        backgroundColor: colors.bgSurface,
        borderRadius: radius.lg,
        boxShadow: shadows.sidebar,
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: spacing.md,
          borderBottom: `1px solid ${colors.borderSoft}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h3
          style={{
            margin: 0,
            fontSize: '18px',
            fontWeight: 600,
            color: colors.textPrimary,
          }}
        >
          Агент PO Workspace
        </h3>
        <button
          onClick={onClose}
          style={{
            padding: '4px 8px',
            backgroundColor: colors.bgHover,
            border: 'none',
            borderRadius: radius.sm,
            cursor: 'pointer',
            color: colors.textSecondary,
          }}
        >
          ✕
        </button>
      </div>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: spacing.md,
          backgroundColor: colors.bgPage,
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              textAlign: 'center',
              color: colors.textMuted,
              marginTop: spacing.lg,
            }}
          >
            <p>Задайте вопрос агенту о задачах, спринтах, команде или качестве</p>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              style={{
                marginBottom: spacing.sm,
                display: 'flex',
                flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
              }}
            >
              <div
                style={{
                  maxWidth: '80%',
                  padding: spacing.sm,
                  backgroundColor: msg.role === 'user' ? colors.accentPrimary : colors.bgSurface,
                  color: msg.role === 'user' ? '#fff' : colors.textPrimary,
                  borderRadius: radius.md,
                  fontSize: '14px',
                  lineHeight: '1.5',
                }}
              >
                {msg.content}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div
        style={{
          padding: spacing.md,
          borderTop: `1px solid ${colors.borderSoft}`,
          display: 'flex',
          gap: spacing.sm,
        }}
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Задайте вопрос агенту..."
          style={{
            flex: 1,
            padding: '10px 14px',
            border: `1px solid ${colors.borderDefault}`,
            borderRadius: radius.md,
            fontSize: '14px',
            outline: 'none',
          }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim()}
          style={{
            padding: '10px 20px',
            backgroundColor: input.trim() ? colors.accentPrimary : colors.borderSoft,
            color: '#fff',
            border: 'none',
            borderRadius: radius.md,
            cursor: input.trim() ? 'pointer' : 'not-allowed',
            fontWeight: 600,
          }}
        >
          Отправить
        </button>
      </div>
    </div>
  )
}
