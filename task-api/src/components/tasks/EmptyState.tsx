import React from 'react'
import { colors, spacing } from '../../styles'
import { Task } from '../../types/task'
import TaskStatusBadge from './TaskStatusBadge'

interface EmptyStateProps {
  onResetFilters?: () => void
}

export function EmptyState({ onResetFilters }: EmptyStateProps) {
  return (
    <div 
      className="card"
      style={{
        textAlign: 'center',
        padding: spacing.xxl,
        backgroundColor: '#ffffff',
      }}
    >
      <div style={{ fontSize: '48px', marginBottom: spacing.sm }}>
        📭
      </div>
      <h3 style={{ color: colors.textPrimary, marginBottom: spacing.xs }}>
        Задачи не найдены
      </h3>
      <p style={{ color: colors.textSecondary, marginBottom: spacing.lg }}>
        Попробуйте изменить фильтры или синхронизировать данные с AS21.
      </p>
      {onResetFilters && (
        <button
          onClick={onResetFilters}
          style={{
            backgroundColor: '#315fa8',
            color: '#ffffff',
            padding: '8px 16px',
          }}
        >
          Сбросить фильтры
        </button>
      )}
    </div>
  )
}

export default EmptyState
