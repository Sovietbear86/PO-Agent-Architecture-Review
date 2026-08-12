import React from 'react'
import { colors, spacing, typography, radius } from '../../styles'

interface EmptyStateProps {
  onResetFilters?: () => void
}

export function EmptyState({ onResetFilters }: EmptyStateProps) {
  return (
    <div style={{
      padding: spacing.xxl,
      textAlign: 'center',
      color: colors.textMuted,
    }}>
      <svg
        width="64"
        height="64"
        viewBox="0 0 24 24"
        fill="none"
        stroke={colors.textMuted}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ marginBottom: spacing.lg }}
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
      <h3 style={{ ...typography.h4, color: colors.textPrimary, marginBottom: spacing.sm }}>
        Нет задач
      </h3>
      <p style={{ marginBottom: spacing.md }}>
        Попробуйте изменить фильтры или синхронизировать задачи из SWTR
      </p>
      {onResetFilters && (
        <button
          onClick={onResetFilters}
          style={{
            padding: '8px 16px',
            backgroundColor: colors.accentPrimary,
            color: '#ffffff',
            border: 'none',
            borderRadius: radius.sm,
            cursor: 'pointer',
          }}
        >
          Сбросить фильтры
        </button>
      )}
    </div>
  )
}
