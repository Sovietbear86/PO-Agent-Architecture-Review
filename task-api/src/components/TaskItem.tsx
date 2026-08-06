import { Task, Status } from '../types/task'
import { statusColors } from '../styles/statusColors'

interface TaskItemProps {
  task: Task
  onUpdate: (id: string, status: Status) => void
  onDelete: (id: string) => void
}

const statusLabels: Record<string, string> = {
  'todo': 'Новая',
  'done': 'Готово',
  'Resolved': 'Решена',
  'resolved': 'Решена',
  'Closed': 'Закрыта',
  'closed': 'Закрыта',
  'Cancelled': 'Отменена',
  'cancelled': 'Отменена',
  'Закрыт': 'Закрыт',
  'Решен': 'Решен',
  'Open': 'Открыта',
  'open': 'Открыта',
  'Ready for review': 'Готова к ревью',
  'ready_for_review': 'Готова к ревью',
  'Ready for QA': 'Готова к тестированию',
  'ready_for_qa': 'Готова к тестированию',
  'Need info': 'Нужна инфа',
  'need_info': 'Нужна инфа',
  'Бэклог': 'Бэклог',
  'backlog': 'Бэклог',
  'Зарегистрирован': 'Зарегистрирован',
  'In progress': 'В работе',
  'in_progress': 'В работе',
  'In review': 'На ревью',
  'in_review': 'На ревью',
  'QA': 'Тестирование',
  'qa': 'Тестирование',
  'Тестирование': 'Тестирование',
  'planning': 'Планирование',
  'need discovery': 'Нужно исследовать',
  'Ready for review': 'Готова к ревью',
  'Ready for QA': 'Готова к тестированию',
}

export default function TaskItem({
  task,
  onUpdate,
  onDelete,
}: TaskItemProps) {
  const handleStatusChange = (newStatus: string) => {
    onUpdate(task.id, newStatus as Status)
  }

  const cardStyle: React.CSSProperties = {
    padding: '16px',
    marginBottom: '8px',
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    border: '1px solid #d9dee8',
    cursor: 'pointer',
    transition: 'box-shadow 0.2s',
  }

  const statusColor = statusColors[task.status] || '#999'
  const statusLabel = statusLabels[task.status] || task.status

  return (
    <div style={cardStyle} onClick={() => handleStatusChange(task.status)}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <span
          style={{
            padding: '4px 12px',
            backgroundColor: statusColor,
            color: '#ffffff',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: 500,
          }}
        >
          {statusLabel}
        </span>
        {task.sourceUrl && (
          <span
            style={{
              color: '#315fa8',
              cursor: 'pointer',
            }}
            title="Open in SWTR"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#315fa8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </span>
        )}
      </div>
      <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: '4px' }}>
        {task.title}
      </div>
      {task.assignee && (
        <div style={{ fontSize: '13px', color: '#667085', marginBottom: '4px' }}>
          {task.assignee}
        </div>
      )}
      {task.deadline && (
        <div style={{ fontSize: '12px', color: '#667085' }}>
          Дедлайн: {new Date(task.deadline).toLocaleDateString('ru-RU')}
        </div>
      )}
    </div>
  )
}

export { statusColors, statusLabels }
