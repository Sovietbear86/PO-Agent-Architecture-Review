import React from 'react'
import { colors, spacing, radius } from '../styles'
import { Task } from '../types/task'
import Drawer from './Drawer'

interface TaskDetailsDrawerProps {
  task: Task
  isOpen: boolean
  onClose: () => void
}

export function TaskDetailsDrawer({
  task,
  isOpen,
  onClose
}: TaskDetailsDrawerProps) {
  // Helper function to format date
  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    try {
      return new Date(dateString).toLocaleDateString('ru-RU')
    } catch {
      return '-'
    }
  }

  // Helper function to get status label
  const getStatusLabel = (status: string) => {
    const statusLabels: Record<string, string> = {
      'todo': 'К выполнению',
      'in_progress': 'В работе',
      'done': 'Выполнено',
      'open': 'Открыта',
      'in_review': 'На проверке',
      'ready_for_review': 'Готова к проверке',
      'ready_for_qa': 'Готова для QA',
      'qa': 'QA',
      'need_info': 'Требуется информация',
      'resolved': 'Решена',
      'closed': 'Закрыта',
      'cancelled': 'Отменена',
    }
    return statusLabels[status] || status
  }

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={task.sourceType === 'AS21' ? task.sourceCode : 'Локальная задача'}
      width={500}
    >
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: spacing.lg,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
          <span style={{ color: colors.accentPrimary, fontSize: '24px' }}>🔗</span>
          <h3 style={{
            margin: 0,
            fontSize: '18px',
            fontWeight: 600,
            color: colors.textPrimary,
          }}>
            {task.title}
          </h3>
        </div>
        <span style={{
          backgroundColor: '#e0ffe9',
          color: '#45e362',
          padding: '4px 12px',
          borderRadius: radius.full,
          fontSize: '12px',
          fontWeight: 500,
          textTransform: 'uppercase',
        }}>
          {getStatusLabel(task.status)}
        </span>
      </div>

      {/* Basic Info */}
      <div style={{ marginBottom: spacing.lg }}>
        <h4 style={{
          margin: '0 0 ' + spacing.sm,
          fontSize: '14px',
          fontWeight: 600,
          color: colors.textPrimary,
        }}>
          Основная информация
        </h4>
        <div style={{ fontSize: '13px', color: colors.textSecondary }}>
          {task.sourceType === 'AS21' && (
            <div style={{ marginBottom: spacing.sm }}>
              <span style={{ color: colors.textPrimary }}>Source:</span>
              {task.sourceUrl ? (
                <a
                  href={task.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    marginLeft: spacing.xs,
                    color: colors.accentPrimary,
                    textDecoration: 'none',
                  }}
                  onClick={(e) => e.stopPropagation()}
                >
                  {task.sourceUrl}
                </a>
              ) : task.sourceData ? (
                // Build SWTR URL from source_data if sourceUrl is not available
                (() => {
                  const space = task.sourceData.swtr_space
                  const code = task.source_id || task.sourceData.swtr_code
                  if (space && code) {
                    const url = `https://portal.works.prod.sbt/swtr/units/all/unit/${code}?space=${space}&tenant=default`
                    return (
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{
                          marginLeft: spacing.xs,
                          color: colors.accentPrimary,
                          textDecoration: 'none',
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {url}
                      </a>
                    )
                  }
                  return <span style={{ marginLeft: spacing.xs }}>Нет ссылки</span>
                })()
              ) : (
                <span style={{ marginLeft: spacing.xs }}>Нет ссылки</span>
              )}
            </div>
          )}
          <div style={{ marginBottom: spacing.sm }}>
            <span style={{ color: colors.textPrimary }}>Assignee:</span>
            <span style={{ marginLeft: spacing.xs }}>
              {task.assignee || 'Не назначено'}
            </span>
          </div>
          <div style={{ marginBottom: spacing.sm }}>
            <span style={{ color: colors.textPrimary }}>Deadline:</span>
            <span style={{ 
              marginLeft: spacing.xs, 
              color: task.deadline ? '#e74c3c' : colors.textSecondary 
            }}>
              {formatDate(task.deadline)}
            </span>
          </div>
          <div>
            <span style={{ color: colors.textPrimary }}>Created:</span>
            <span style={{ marginLeft: spacing.xs }}>
              {formatDate(task.createdAt || task.created_at)}
            </span>
          </div>
        </div>
      </div>

      {/* Description */}
      {task.description && (
        <div style={{ marginBottom: spacing.lg }}>
          <h4 style={{
            margin: '0 0 ' + spacing.sm,
            fontSize: '14px',
            fontWeight: 600,
            color: colors.textPrimary,
          }}>
            Описание
          </h4>
          <div style={{
            fontSize: '13px',
            color: colors.textSecondary,
            lineHeight: '1.6',
            backgroundColor: '#f8f9fa',
            padding: spacing.sm,
            borderRadius: radius.md,
          }}>
            {task.description}
          </div>
        </div>
      )}

      {/* Product & Source Info */}
      <div>
        <h4 style={{
          margin: '0 0 ' + spacing.sm,
          fontSize: '14px',
          fontWeight: 600,
          color: colors.textPrimary,
        }}>
          Дополнительно
        </h4>
        <div style={{ fontSize: '13px', color: colors.textSecondary }}>
          {task.product && (
            <div style={{ marginBottom: spacing.sm }}>
              <span style={{ color: colors.textPrimary }}>Product:</span>
              <span style={{
                marginLeft: spacing.xs,
                backgroundColor: '#e0ffe9',
                color: '#45e362',
                padding: '2px 8px',
                borderRadius: radius.full,
                fontSize: '11px',
              }}>
                {task.product}
              </span>
            </div>
          )}
          {task.sprint && (
            <div style={{ marginBottom: spacing.sm }}>
              <span style={{ color: colors.textPrimary }}>Sprint:</span>
              <span style={{
                marginLeft: spacing.xs,
                color: colors.accentPrimary,
                fontWeight: 500,
              }}>
                {task.sprint}
              </span>
            </div>
          )}
          <div>
            <span style={{ color: colors.textPrimary }}>Updated:</span>
            <span style={{ marginLeft: spacing.xs }}>
              {formatDate(task.updatedAt || task.updated_at)}
            </span>
          </div>
        </div>
      </div>
    </Drawer>
  )
}

export default TaskDetailsDrawer
