import { Task } from '../../types/Task'
import { TaskCard } from './TaskCard'
import { EmptyState } from './EmptyState'

interface TaskListProps {
  tasks: Task[]
  onOpenDetails?: (task: Task) => void
  onStatusChange?: (taskId: string, status: string) => void
  compact?: boolean
}

export function TaskList({
  tasks,
  onOpenDetails,
  onStatusChange,
  compact = false
}: TaskListProps) {
  if (tasks.length === 0) {
    return <EmptyState onResetFilters={undefined} />
  }

  return (
    <div>
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onOpenDetails={onOpenDetails}
          onStatusChange={onStatusChange}
          compact={compact}
        />
      ))}
    </div>
  )
}
