import React from 'react'
import { colors, spacing, radius } from '../../styles'

interface AgentButtonProps {
  onClick: () => void
  isExecuting?: boolean
}

export function AgentButton({ onClick, isExecuting = false }: AgentButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={isExecuting}
      style={{
        padding: '8px 16px',
        backgroundColor: isExecuting ? colors.statusWarning : colors.accentPrimary,
        color: '#ffffff',
        border: 'none',
        borderRadius: radius.md,
        cursor: isExecuting ? 'not-allowed' : 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: spacing.xs,
        fontWeight: 600,
        fontSize: '14px',
      }}
      title="Открыть чат с агентом"
    >
      {isExecuting ? (
        <>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
          Обработка...
        </>
      ) : (
        <>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          Агент
        </>
      )}
    </button>
  )
}
