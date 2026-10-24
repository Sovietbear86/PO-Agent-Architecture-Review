import { useState, useEffect, useMemo } from 'react'
import { api, tasks as taskApi } from '../api'
import { AppShell, Sidebar, SidebarItem, TopBar, FilterBar, TaskList } from '../components'
import type { Task } from '../types'

export function TasksView() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<{ status: string[], assignee: string[], sprint: string[], space: string[] }>({
    status: [],
    assignee: [],
    sprint: [],
    space: []
  })
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  useEffect(() => {
    const loadTasks = async () => {
      try {
        const response = await taskApi.getAll({})
        setTasks(response.data)
      } catch (error) {
        console.error('Failed to load tasks:', error)
      } finally {
        setLoading(false)
      }
    }
    loadTasks()
  }, [])

  // Extract unique values for filters
  const assignees = useMemo(() => {
    return Array.from(new Set(tasks.map((t) => t.assignee).filter(Boolean)))
  }, [tasks])

  const sprints = useMemo(() => {
    return Array.from(new Set(tasks.map((t) => t.sprint).filter(Boolean)))
  }, [tasks])

  const spaces = useMemo(() => {
    return Array.from(new Set(tasks.map((t) => t.space).filter(Boolean)))
  }, [tasks])

  // Filter tasks based on filter state
  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => {
      // Status filter
      if (filter.status.length > 0 && !filter.status.includes(task.status)) {
        return false
      }
      // Assignee filter
      if (filter.assignee.length > 0 && !filter.assignee.includes(task.assignee || '')) {
        return false
      }
      // Sprint filter
      if (filter.sprint.length > 0 && !filter.sprint.includes(task.sprint || '')) {
        return false
      }
      // Space filter
      if (filter.space.length > 0 && !filter.space.includes(task.space || '')) {
        return false
      }
      return true
    })
  }, [tasks, filter])

  const handleStatusChange = (status: string | string[]) => {
    setFilter(prev => ({ ...prev, status: Array.isArray(status) ? status : [] as string[] }))
  }

  const handleAssigneeChange = (assignee: string | string[]) => {
    setFilter(prev => ({ ...prev, assignee: Array.isArray(assignee) ? assignee : [] as string[] }))
  }

  const handleSprintChange = (sprint: string | string[]) => {
    setFilter(prev => ({ ...prev, sprint: Array.isArray(sprint) ? sprint : [] as string[] }))
  }

  const handleSpaceChange = (space: string | string[]) => {
    setFilter(prev => ({ ...prev, space: Array.isArray(space) ? space : [] as string[] }))
  }

  if (loading) return <div className="p-4">Loading...</div>

  return (
    <Layout
      sidebar={
        <Sidebar>
          <SidebarItem label="Обзор" onClick={() => window.location.href = '/'} />
          <SidebarItem label="Задачи" active />
          <SidebarItem label="Спринты" onClick={() => window.location.href = '/sprint'} />
          <SidebarItem label="Релизы" onClick={() => window.location.href = '/releases'} />
          <SidebarItem label="Команда" onClick={() => window.location.href = '/team'} />
          <SidebarItem label="Аналитика" onClick={() => window.location.href = '/quality'} />
          <SidebarItem label="История" onClick={() => window.location.href = '/history'} />
        </Sidebar>
      }
      content={
        <div style={{ flex: 1 }}>
          <TopBar
            title="Задачи"
            subtitle="Управление задачами в SWTR"
            rightContent={null}
          />

          {/* Filter Bar */}
          <div style={{
            position: 'sticky',
            top: '64px',
            zIndex: 100,
            backgroundColor: '#ffffff',
            border: '1px solid #d9dee8',
            borderRadius: '8px',
            padding: '1rem',
            marginRight: '1rem',
            marginBottom: '1rem',
          }}>
            <FilterBar
              status={filter.status}
              onStatusChange={handleStatusChange}
              assignee={filter.assignee}
              onAssigneeChange={handleAssigneeChange}
              assignees={assignees}
              sprint={filter.sprint}
              onSprintChange={handleSprintChange}
              sprints={sprints}
              space={filter.space}
              onSpaceChange={handleSpaceChange}
              spaces={spaces}
            />
          </div>

          {/* Task List */}
          <div style={{ marginTop: '1rem', marginRight: '1rem' }}>
            <TaskList
              tasks={filteredTasks}
              onOpenDetails={(task) => setSelectedTask(task)}
            />
          </div>
        </div>
      }
    />
  )
}

export default TasksView
