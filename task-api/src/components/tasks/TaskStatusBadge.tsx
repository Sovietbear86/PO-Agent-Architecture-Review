import React from 'react'
import { colors } from '../../styles'
import { StatusType } from '../../types/task'

interface TaskStatusBadgeProps {
  status: StatusType | string
  workflowStatusName?: string
  compact?: boolean
}

// Map of status values to CSS classes
const statusClasses: Record<string, string> = {
  'todo': 'badge-todo',
  'done': 'badge-done',
  'Resolved': 'badge-Resolved',
  'resolved': 'badge-resolved',
  'Closed': 'badge-Closed',
  'closed': 'badge-closed',
  'Cancelled': 'badge-Cancelled',
  'cancelled': 'badge-cancelled',
  'Open': 'badge-Open',
  'open': 'badge-open',
  'Ready for review': 'badge-Ready-for-review',
  'ready_for_review': 'badge-ready-for-review',
  'Ready for QA': 'badge-Ready-for-QA',
  'ready_for_qa': 'badge-ready-for-qa',
  'Need info': 'badge-Need-info',
  'need_info': 'badge-need-info',
  'In progress': 'badge-In-progress',
  'in_progress': 'badge-in-progress',
  'In review': 'badge-In-review',
  'in_review': 'badge-in-review',
  'QA': 'badge-QA',
  'qa': 'badge-qa',
  'Тестирование': 'badge-Тестирование',
  'planning': 'badge-Planning',
  'need discovery': 'badge-Need-discovery',
  'Бэклог': 'badge-Бэклог',
  'backlog': 'badge-backlog',
  'Закрыт': 'badge-Закрыт',
  'Решен': 'badge-Решен',
  'Зарегистрирован': 'badge-Зарегистрирован',
  'Local': 'badge-local',
}

export function TaskStatusBadge({ status, workflowStatusName, compact = false }: TaskStatusBadgeProps) {
  // Use workflowStatusName if available, otherwise use status
  const badgeText = workflowStatusName || status
  const badgeClass = statusClasses[badgeText] || 'badge-local'

  const badgeStyle: React.CSSProperties = compact
    ? {
        padding: '2px 6px',
        borderRadius: '4px',
        fontSize: '11px',
      }
    : {
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '12px',
      }

  return (
    <span
      className={`badge ${badgeClass}`}
      style={badgeStyle}
    >
      {badgeText}
    </span>
  )
}

export default TaskStatusBadge
