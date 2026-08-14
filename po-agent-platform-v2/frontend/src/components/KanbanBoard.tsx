import { useState, useMemo } from 'react'
import type { Task } from '../types'
import { api, tasks as taskApi } from '../api'

type ColumnId = 'todo' | 'in_progress' | 'review' | 'done'

interface Column {
  id: ColumnId
  title: string
  color: string
}

const COLUMNS: Column[] = [
  { id: 'todo', title: 'To Do', color: 'bg-gray-100 border-gray-300' },
  { id: 'in_progress', title: 'In Progress', color: 'bg-blue-50 border-blue-300' },
  { id: 'review', title: 'Review', color: 'bg-purple-50 border-purple-300' },
  { id: 'done', title: 'Done', color: 'bg-green-50 border-green-300' },
]

export function KanbanBoard() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)

  useMemo(() => {
    const loadTasks = async () => {
      try {
        const response = await taskApi.getAll()
        setTasks(response.data)
      } catch (error) {
        console.error('Failed to load tasks:', error)
      } finally {
        setLoading(false)
      }
    }
    loadTasks()
  }, [])

  const getTasksByStatus = (status: string) => {
    return tasks.filter((t) => t.status === status)
  }

  const statusMap: Record<string, ColumnId> = {
    todo: 'todo',
    in_progress: 'in_progress',
    review: 'review',
    done: 'done',
  }

  const updateTaskStatus = async (taskId: string, newStatus: string) => {
    try {
      await taskApi.updateStatus(taskId, newStatus)
      setTasks((prev) =>
        prev.map((t) =>
          t.id === taskId ? { ...t, status: newStatus } : t
        )
      )
    } catch (error) {
      console.error('Failed to update task:', error)
    }
  }

  if (loading) return <div className="p-4">Loading board...</div>

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {COLUMNS.map((column) => (
        <div
          key={column.id}
          className={`flex-1 min-w-[280px] rounded-lg border-2 ${column.color} p-3`}
        >
          <div className="flex justify-between items-center mb-3 pb-2 border-b">
            <h3 className="font-semibold text-gray-700">{column.title}</h3>
            <span className="bg-gray-200 text-gray-600 text-xs px-2 py-1 rounded-full">
              {getTasksByStatus(column.id).length}
            </span>
          </div>
          <div className="space-y-2">
            {getTasksByStatus(column.id).map((task) => (
              <div
                key={task.id}
                className="bg-white p-3 rounded shadow-sm border border-gray-200 cursor-pointer hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-2">
                  <span className="font-mono text-xs text-gray-500">{task.id}</span>
                  {task.deadline && (
                    <span className="text-xs text-red-500 font-medium">
                      {task.deadline.split('T')[0]}
                    </span>
                  )}
                </div>
                <h4 className="font-medium text-gray-800 mb-1">{task.title}</h4>
                {task.assignee && (
                  <p className="text-sm text-gray-600 mb-2">
                    {task.assignee}
                  </p>
                )}
                {task.description && (
                  <p className="text-xs text-gray-500 line-clamp-2">
                    {task.description}
                  </p>
                )}
                {column.id !== 'done' && (
                  <div className="mt-3 pt-2 border-t flex justify-between gap-1">
                    <button
                      onClick={() => updateTaskStatus(task.id, 'in_progress')}
                      className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                    >
                      Start
                    </button>
                    <button
                      onClick={() => updateTaskStatus(task.id, 'done')}
                      className="text-xs px-2 py-1 bg-green-50 text-green-600 rounded hover:bg-green-100"
                    >
                      Done
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

export default KanbanBoard
