import React from 'react'
import { colors, spacing, radius, spaceColors } from '../../styles'
import { Task } from '../../types/Task'

interface TaskCardProps {
  task: Task
  onOpenDetails?: (task: Task) => void
  onStatusChange?: (taskId: string, status: string) => void
  compact?: boolean
}

export function TaskCard({
  task,
  onOpenDetails,
  onStatusChange,
  compact = false
}: TaskCardProps) {
  // Always use chain icon for all tasks
  const sourceIcon = '🔗'
  const sourceColor = colors.accentPrimary
  const productColor = colors.accentPrimary

  // Open SWTR URL if available
  const handleOpenSwtr = (e: React.MouseEvent) => {
    e.stopPropagation()

    // Build SWTR URL from source_data if sourceUrl is not available
    let url = task.sourceUrl
    if (!url && task.sourceData) {
      const space = task.sourceData.swtr_space
      const code = task.source_id || task.sourceData.swtr_code
      if (space && code) {
        url = `https://portal.works.prod.sbt/swtr/units/all/unit/${code}?space=${space}&tenant=default`
      }
    }

    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  // Helper function to get date string (supports both camelCase and snake_case)
  const getDateValue = (dateField?: string | Date, snakeCaseField?: string) => {
    if (dateField) return dateField
    if (snakeCaseField && (task as any)[snakeCaseField]) return (task as any)[snakeCaseField]
    return undefined
  }

  // Handle card click to open details
  const handleCardClick = () => {
    if (onOpenDetails) {
      onOpenDetails(task)
    }
  }

  const cardStyle: React.CSSProperties = compact
    ? {
        padding: '8px',
        marginBottom: spacing.xs,
      }
    : {
        padding: '12px',
        marginBottom: spacing.sm,
      }

  return (
    <div
      className="card"
      style={{
        ...cardStyle,
        height: 'auto',
        cursor: onOpenDetails ? 'pointer' : 'default',
        border: '1px solid #d9dee8',
      }}
      onClick={handleCardClick}
    >
      {/* Header row - icon on left, title and status on right */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: spacing.sm,
        marginBottom: spacing.sm,
      }}>
        <span
          style={{
            color: sourceColor,
            fontSize: '16px',
            cursor: task.sourceUrl ? 'pointer' : 'default',
            flexShrink: 0,
          }}
          onClick={handleOpenSwtr}
          title={task.sourceUrl ? 'Open in SWTR' : 'Local task'}
        >
          {sourceIcon}
        </span>
        <div style={{ flex: 1 }}>
          {/* Title */}
          <h4
            style={{
              margin: '0 0 ' + spacing.xs,
              fontSize: compact ? '15px' : '16px',
              color: colors.textPrimary,
              fontWeight: 600,
            }}
          >
            {task.title}
          </h4>

          {/* Product badge */}
          {task.product && (
            <span
              style={{
                backgroundColor: `${productColor}20`,
                color: productColor,
                padding: '2px 8px',
                borderRadius: radius.full,
                fontSize: '11px',
                fontWeight: 500,
                marginRight: spacing.xs,
              }}
            >
              {task.product}
            </span>
          )}

          {/* Space badge */}
          {task.space && (
            <span
              style={{
                backgroundColor: `${spaceColors[task.space] || '#999'}20`,
                color: spaceColors[task.space] || '#666',
                padding: '2px 8px',
                borderRadius: radius.full,
                fontSize: '11px',
                fontWeight: 500,
              }}
            >
              {task.space}
            </span>
          )}
        </div>
      </div>

      {/* Meta row - status, assignee, dates */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: spacing.sm,
        flexWrap: 'wrap',
      }}>
        {/* Status badge */}
        <span
          style={{
            backgroundColor: `${colors.accentSoft}`,
            color: colors.accentPrimary,
            padding: '2px 8px',
            borderRadius: radius.sm,
            fontSize: '11px',
            fontWeight: 500,
          }}
        >
          {task.status || 'unknown'}
        </span>

        {/* Assignee */}
        {task.assignee && (
          <span
            style={{
              color: colors.textSecondary,
              fontSize: '12px',
            }}
          >
            {task.assignee}
          </span>
        )}

        {/* Deadline */}
        {task.deadline && (
          <span
            style={{
              color: colors.textMuted,
              fontSize: '11px',
            }}
          >
            📅 {new Date(task.deadline).toLocaleDateString('ru-RU')}
          </span>
        )}
      </div>

      {/* Description preview */}
      {task.description && (
        <div
          style={{
            marginTop: spacing.sm,
            fontSize: '13px',
            color: colors.textSecondary,
            lineHeight: '1.5',
            WebkitLineClamp: 2,
            display: '-webkit-box',
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
          }}
        >
          {task.description}
        </div>
      )}
    </div>
  )
}
