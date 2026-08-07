import { useCallback, useMemo, useState, useEffect } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { Task, CreateTaskInput, UpdateTaskInput } from '../types/task'
import { useLocalStorage } from './useLocalStorage'

/** Validate title length */
function validateTitle(title: string): string | null {
  if (title.length < 1) {
    return 'Title must be at least 1 character'
  }
  if (title.length > 200) {
    return 'Title must be 200 characters or less'
  }
  return null
}

/** Validate description length */
function validateDescription(description?: string): string | null {
  if (description && description.length > 1000) {
    return 'Description must be 1000 characters or less'
  }
  return null
}

/** Validate assignee length */
function validateAssignee(assignee?: string): string | null {
  if (assignee && assignee.length > 100) {
    return 'Assignee must be 100 characters or less'
  }
  return null
}

/** Hook for managing task operations. */
export function useTasks() {
  const { tasks: localStorageTasks, save: localStorageSave } = useLocalStorage()
  const [tasks, setTasks] = useState<Task[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isUsingLocalStorage, setIsUsingLocalStorage] = useState(false)

  // Load tasks from API on mount
  useEffect(() => {
    const isTest = typeof window === 'undefined' || process.env.NODE_ENV === 'test'
    if (isTest) {
      console.log('Testing environment, using localStorage')
      setTasks(localStorageTasks)
      setIsUsingLocalStorage(true)
      return
    }

    const loadTasks = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const { getTasks } = await import('../api/client')
        const apiData = await getTasks()
        console.log('Loaded tasks from API:', apiData.length, 'tasks')
        setTasks(apiData)
        setIsUsingLocalStorage(false)
        // Also save to localStorage for offline use
        localStorageSave(apiData)
      } catch (err) {
        console.warn('API failed, using localStorage:', err)
        setTasks(localStorageTasks)
        setIsUsingLocalStorage(true)
      } finally {
        setIsLoading(false)
      }
    }
    loadTasks()
  }, [localStorageTasks])

  const addTask = useCallback((input: CreateTaskInput): Task => {
    const now = new Date().toISOString()
    const newTask: Task = {
      id: uuidv4(),
      title: input.title,
      description: input.description,
      assignee: input.assignee,
      sourceUrl: input.sourceUrl,
      status: 'todo',
      createdAt: now,
      updatedAt: now,
    }

    // Update local state
    setTasks(prev => [...prev, newTask])

    // Save to localStorage (also syncs API if available)
    localStorageSave([...tasks, newTask])

    return newTask
  }, [tasks, localStorageSave])

  const updateTask = useCallback((id: string, input: UpdateTaskInput): Task | null => {
    // Validate title if being updated
    if (input.title !== undefined) {
      const titleError = validateTitle(input.title)
      if (titleError) {
        console.error(titleError)
        return null
      }
    }

    // Validate description if being updated
    if (input.description !== undefined) {
      const descError = validateDescription(input.description)
      if (descError) {
        console.error(descError)
        return null
      }
    }

    // Validate assignee if being updated
    if (input.assignee !== undefined) {
      const assigneeError = validateAssignee(input.assignee)
      if (assigneeError) {
        console.error(assigneeError)
        return null
      }
    }

    const taskIndex = tasks.findIndex((t) => t.id === id)
    if (taskIndex === -1) return null

    const task = tasks[taskIndex]
    const now = new Date().toISOString()
    const updatedTask: Task = {
      ...task,
      ...input,
      updatedAt: now,
    }

    const newTasks = [...tasks]
    newTasks[taskIndex] = updatedTask

    // Update local state
    setTasks(newTasks)

    // Save to localStorage
    localStorageSave(newTasks)

    return updatedTask
  }, [tasks, localStorageSave])

  const deleteTask = useCallback((id: string): boolean => {
    const taskIndex = tasks.findIndex((t) => t.id === id)
    if (taskIndex === -1) return false

    const newTasks = tasks.filter((t) => t.id !== id)

    // Update local state
    setTasks(newTasks)

    // Save to localStorage
    localStorageSave(newTasks)

    return true
  }, [tasks, localStorageSave])

  const filterTasks = useCallback((filters: {
    status?: string | string[]
    assignee?: string | string[]
    sprint?: string | string[]
    space?: string | string[]
  }): Task[] => {
    // Helper to get status for filtering - prefer workflow_status.code from sourceData
    const getTaskStatus = (task: Task): string => {
      // Try to get status code from swtr_attributes first (more reliable)
      if (task.sourceData?.swtr_attributes) {
        const attrs = task.sourceData.swtr_attributes as Array<{ code: string; value?: any }>;
        const statusAttr = attrs.find(attr => attr.code === 'workflow_status');
        if (statusAttr && statusAttr.value && typeof statusAttr.value === 'object') {
          const code = statusAttr.value.code;
          if (code) return code.toLowerCase();
        }
      }
      // Fallback to workflowStatusName
      if (task.sourceData?.workflowStatusName) {
        return task.sourceData.workflowStatusName.toLowerCase()
      }
      if (task.sourceData?.workflowStatus) {
        return task.sourceData.workflowStatus.toLowerCase()
      }
      return task.status?.toString().toLowerCase() || 'todo'
    }

    // Handle multiple statuses
    const statusFilter = Array.isArray(filters.status)
      ? filters.status.map(s => s.toString().toLowerCase())
      : filters.status ? [filters.status.toString().toLowerCase()] : null

    // Handle multiple assignees - 'all' means no filter
    let assigneeFilter: string[] | null = null
    if (filters.assignee && filters.assignee !== 'all') {
      if (Array.isArray(filters.assignee) && filters.assignee.length > 0) {
        assigneeFilter = filters.assignee.map(a => a.toString().toLowerCase())
      } else if (typeof filters.assignee === 'string' && filters.assignee) {
        assigneeFilter = [filters.assignee.toString().toLowerCase()]
      }
    }

    // Handle multiple sprints - 'all' means no filter, 'none' means tasks without sprint
    let sprintFilter: string[] | null = null
    let filterWithoutSprint = false
    if (filters.sprint && filters.sprint !== 'all') {
      if (Array.isArray(filters.sprint) && filters.sprint.length > 0) {
        sprintFilter = filters.sprint.map(s => s.toString().toLowerCase())
        // Check if 'none' is in the filter
        filterWithoutSprint = sprintFilter.includes('none')
        // Remove 'none' from sprintFilter
        if (filterWithoutSprint) {
          sprintFilter = sprintFilter.filter(s => s !== 'none')
        }
      } else if (typeof filters.sprint === 'string' && filters.sprint) {
        if (filters.sprint.toLowerCase() === 'none') {
          filterWithoutSprint = true
        } else {
          sprintFilter = [filters.sprint.toLowerCase()]
        }
      }
    }

    // Handle multiple spaces - 'all' means no filter
    let spaceFilter: string[] | null = null
    if (filters.space && filters.space !== 'all') {
      if (Array.isArray(filters.space) && filters.space.length > 0) {
        spaceFilter = filters.space
      } else if (typeof filters.space === 'string' && filters.space) {
        spaceFilter = [filters.space]
      }
    }

    return tasks.filter((task) => {
      const taskStatus = getTaskStatus(task)
      if (statusFilter && !statusFilter.includes(taskStatus)) {
        return false
      }
      if (assigneeFilter && task.assignee && !assigneeFilter.includes(task.assignee.toLowerCase())) {
        return false
      }
      // If sprintFilter is set, task must have a sprint and it must match
      if (sprintFilter && sprintFilter.length > 0) {
        if (!task.sprint) {
          return false
        }
        if (!sprintFilter.includes(task.sprint.toLowerCase())) {
          return false
        }
      }
      // If filterWithoutSprint is true, only tasks without sprint pass
      if (filterWithoutSprint && task.sprint) {
        return false
      }
      // Filter by space if filter is set
      if (spaceFilter && spaceFilter.length > 0) {
        const taskSpace = (task.sourceData as any)?.swtr_space ?? (task.sourceData as any)['swtr_space']
        if (!taskSpace || !spaceFilter.includes(taskSpace)) {
          return false
        }
      }
      return true
    })
  }, [tasks])

  const getTaskById = useCallback((id: string): Task | null => {
    return tasks.find((t) => t.id === id) || null
  }, [tasks])

  const updateTaskStatus = useCallback((id: string, status: string): Task | null => {
    return updateTask(id, { status })
  }, [updateTask])

  const assignees = useMemo(() => {
    const assignees = tasks
      .map((t) => t.assignee)
      .filter((a): a is string => !!a)
    return Array.from(new Set(assignees))
  }, [tasks])

  const sprints = useMemo(() => {
    const sprints = tasks
      .map((t) => t.sprint)
      .filter((s): s is string => !!s)
    return Array.from(new Set(sprints))
  }, [tasks])

  const spaces = useMemo(() => {
    const spaces = tasks
      .map((t) => (t.sourceData as any)?.swtr_space ?? (t.sourceData as any)['swtr_space'])
      .filter((s): s is string => !!s)
    return Array.from(new Set(spaces))
  }, [tasks])

  return {
    tasks,
    isLoading,
    error,
    addTask,
    updateTask,
    deleteTask,
    filterTasks,
    getTaskById,
    updateTaskStatus,
    assignees,
    sprints,
    spaces,
  }
}
