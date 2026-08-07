import { useState, useMemo, useCallback } from 'react'
import { CreateTaskInput, Task } from '../types/task'
import { useTasks } from '../hooks/useTasks'
import { FilterBar } from './FilterBar'
import { TaskList } from './TaskList'
import { AgentButton } from './AgentButton'
import { AgentChat } from './AgentChat'
import { colors } from '../styles'
import { Sidebar } from './layout/Sidebar'
import { TopBar } from './layout/TopBar'
import { CreateTaskDrawer } from './CreateTaskDrawer'
import { TaskDetailsDrawer } from './TaskDetailsDrawer'

interface SidebarItemProps {
  label: string
  active?: boolean
  disabled?: boolean
  onClick?: () => void
  icon?: React.ReactNode
}

function SidebarItem({ label, active = false, disabled = false, onClick, icon }: SidebarItemProps) {
  return (
    <li
      className={`sidebar-nav-item ${active ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
      onClick={disabled ? undefined : onClick}
      style={{
        backgroundColor: active ? colors.bgSelected : 'transparent',
        color: active ? colors.accentPrimary : colors.textSecondary,
      }}
    >
      {icon && <span style={{ fontSize: '16px' }}>{icon}</span>}
      <span>{label}</span>
    </li>
  )
}

export function App() {
  const {
    tasks,
    addTask,
    updateTaskStatus,
    deleteTask,
    filterTasks,
    assignees,
    sprints,
    spaces,
  } = useTasks()

  console.log('App - tasks:', tasks.length, 'tasks')
  console.log('App - assignees:', assignees)
  console.log('App - sprints:', sprints)
  console.log('App - spaces:', spaces)

  const [filterStatus, setFilterStatus] = useState<string | string[]>([])
  const [filterAssignee, setFilterAssignee] = useState<string | string[]>([])
  const [filterSprint, setFilterSprint] = useState<string | string[]>([])
  const [filterSpace, setFilterSpace] = useState<string | string[]>([])
  const [isSyncing, setIsSyncing] = useState(false)
  const [isDrawerOpen, setIsDrawerOpen] = useState(false)
  const [isAgentOpen, setIsAgentOpen] = useState(false)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  const filteredTasks = useMemo(() => {
    // Handle multiple statuses - filterTasks accepts string | string[]
    const statusValue: string | string[] | undefined =
      Array.isArray(filterStatus)
        ? filterStatus.length === 0 ? undefined : filterStatus
        : filterStatus === 'all' || filterStatus === '' ? undefined : filterStatus
    // Sprint filter: undefined if empty, 'all' if explicitly 'all', otherwise the value
    const sprintValue: string | string[] | undefined =
      !filterSprint || (Array.isArray(filterSprint) && filterSprint.length === 0) ? undefined :
      filterSprint === 'all' ? 'all' : filterSprint
    // Space filter: undefined if empty, 'all' if explicitly 'all', otherwise the value
    const spaceValue: string | string[] | undefined =
      !filterSpace || (Array.isArray(filterSpace) && filterSpace.length === 0) ? undefined :
      filterSpace === 'all' ? 'all' : filterSpace
    const result = filterTasks({ status: statusValue, assignee: filterAssignee || undefined, sprint: sprintValue, space: spaceValue })
    console.log('App - filteredTasks:', result.length, 'tasks')
    console.log('App - filterSprint:', filterSprint, '->', sprintValue)
    console.log('App - filterSpace:', filterSpace, '->', spaceValue)
    return result
  }, [tasks, filterStatus, filterAssignee, filterSprint, filterSpace, filterTasks])

  const handleAddTask = (data: CreateTaskInput) => {
    addTask(data)
    setIsDrawerOpen(false)
  }

  const handleUpdateStatus = useCallback((id: string, status: string) => {
    updateTaskStatus(id, status)
  }, [updateTaskStatus])

  const handleDeleteTask = (id: string) => {
    deleteTask(id)
  }

  const handleSync = async () => {
    setIsSyncing(true)
    try {
      const response = await fetch('/api/v1/swtr/sync-user', { method: 'POST' })
      if (response.ok) {
        const data = await response.json()
        // Update tasks with synced data
        if (data.tasks && data.tasks.length > 0) {
          // Tasks are already in the database from sync_team_tasks.py
          // The sync endpoint returns the count, not the tasks
          alert(`Синхронизация завершена. В базе ${data.tasks.length} задач`)
          // Reload page to refresh tasks
          window.location.reload()
        } else {
          alert(`Синхронизация завершена. В базе 0 задач`)
        }
      } else {
        const errorData = await response.json().catch(() => ({}))
        alert(`Ошибка при синхронизации: ${response.status} ${response.statusText}`)
      }
    } catch (error) {
      console.error('Sync error:', error)
      alert('Ошибка при синхронизации: проверьте, что сервер запущен')
    } finally {
      setIsSyncing(false)
    }
  }

  return (
    <>
      <div className="app-shell" style={{ minHeight: '100vh', display: 'flex' }}>
        <Sidebar>
          <SidebarItem label="Обзор" active />
          <SidebarItem label="Задачи" />
          <SidebarItem label="Спринты" disabled />
          <SidebarItem label="Релизы" disabled />
          <SidebarItem label="Команда" disabled />
          <SidebarItem label="Аналитика" disabled />
          <SidebarItem label="Настройки" disabled />
        </Sidebar>

        <main style={{
          flex: 1,
          backgroundColor: colors.bgPage,
          paddingLeft: '230px',
        }}>
          <TopBar
            title="PO Workspace"
            subtitle="Пространство владельца продукта"
            rightContent={
              <>
                <button
                  onClick={handleSync}
                  disabled={isSyncing}
                  title="Синхронизировать задачи из SWTR"
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#ffffff',
                    color: '#20242c',
                    border: '1px solid #d9dee8',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                  }}
                >
                  {isSyncing ? (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83" />
                        <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8" />
                      </svg>
                      Синхронизация...
                    </>
                  ) : (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M23 4v6h-6" />
                        <path d="M1 20v-6h6" />
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
                      </svg>
                      Синхронизировать
                    </>
                  )}
                </button>
                <button
                  onClick={() => setIsDrawerOpen(true)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: colors.accentPrimary,
                    color: '#ffffff',
                  }}
                >
                  + Создать задачу
                </button>
              </>
            }
          />

          {/* Fixed Filter Bar - same width as TopBar, above task list */}
          <div style={{
            position: 'sticky',
            top: '64px',
            zIndex: 100,
            backgroundColor: '#ffffff',
            border: '1px solid #d9dee8',
            borderRadius: '8px',
            padding: '1rem',
            marginRight: '15px',
            marginBottom: '1rem',
          }}>
            <FilterBar
              status={filterStatus}
              onStatusChange={setFilterStatus}
              assignee={filterAssignee}
              onAssigneeChange={setFilterAssignee}
              assignees={assignees}
              sprint={filterSprint}
              onSprintChange={setFilterSprint}
              sprints={sprints}
              space={filterSpace}
              onSpaceChange={setFilterSpace}
              spaces={spaces}
            />
          </div>

          <div style={{ marginTop: '64px', marginRight: '15px', maxWidth: '1455px' }}>
            <TaskList
              tasks={filteredTasks}
              onOpenDetails={(task) => setSelectedTask(task)}
              onStatusChange={handleUpdateStatus}
              compact={false}
            />
          </div>
        </main>
      </div>

      <CreateTaskDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        onSubmit={handleAddTask}
      />

      <AgentChat
        isOpen={isAgentOpen}
        onClose={() => setIsAgentOpen(false)}
      />

      <AgentButton
        onClick={() => setIsAgentOpen(true)}
        isExecuting={false}
      />

      {selectedTask && (
        <TaskDetailsDrawer
          task={selectedTask}
          isOpen={!!selectedTask}
          onClose={() => setSelectedTask(null)}
        />
      )}
    </>
  )
}
