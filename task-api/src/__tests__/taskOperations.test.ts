/** Tests for task operations - add, update, delete tasks. */
import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useTasks } from '../hooks/useTasks'

describe('Task operations', () => {
  const STORAGE_KEY = 'task-tracker'

  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('addTask', () => {
    it('should add a new task with default status', () => {
      const { result } = renderHook(() => useTasks())

      let newTask: any = null
      act(() => {
        newTask = result.current.addTask({ title: 'New Task' })
      })

      expect(newTask).toBeDefined()
      expect(newTask.title).toBe('New Task')
      expect(newTask.status).toBe('todo')
      expect(newTask.id).toBeDefined()
    })

    it('should add a task with description and assignee', () => {
      const { result } = renderHook(() => useTasks())

      let newTask: any = null
      act(() => {
        newTask = result.current.addTask({
          title: 'Task with details',
          description: 'Detailed description',
          assignee: 'John Doe',
        })
      })

      expect(newTask.description).toBe('Detailed description')
      expect(newTask.assignee).toBe('John Doe')
    })

    it('should persist task to localStorage', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useTasks())

      act(() => {
        result.current.addTask({ title: 'Persisted Task' })
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      expect(stored).toBeDefined()

      const parsed = JSON.parse(stored!)
      expect(parsed.tasks).toHaveLength(1)
      expect(parsed.tasks[0].title).toBe('Persisted Task')
    })

    it('should add multiple tasks with individual act calls', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useTasks())

      let task1: any = null
      let task2: any = null
      let task3: any = null

      act(() => {
        task1 = result.current.addTask({ title: 'Task 1' })
      })
      act(() => {
        task2 = result.current.addTask({ title: 'Task 2' })
      })
      act(() => {
        task3 = result.current.addTask({ title: 'Task 3' })
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      expect(stored).toBeDefined()

      const parsed = JSON.parse(stored!)
      expect(parsed.tasks).toHaveLength(3)
    })
  })

  describe('updateTaskStatus', () => {
    it('should update task status to in_progress', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useTasks())

      let task: any = null
      act(() => {
        task = result.current.addTask({ title: 'Task' })
      })

      act(() => {
        result.current.updateTaskStatus(task.id, 'in_progress')
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      const parsed = JSON.parse(stored!)
      expect(parsed.tasks[0].status).toBe('in_progress')
    })

    it('should update task status to done', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useTasks())

      let task: any = null
      act(() => {
        task = result.current.addTask({ title: 'Task' })
      })

      act(() => {
        result.current.updateTaskStatus(task.id, 'done')
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      const parsed = JSON.parse(stored!)
      expect(parsed.tasks[0].status).toBe('done')
    })
  })

  describe('deleteTask', () => {
    it('should delete existing task', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useTasks())

      let task: any = null
      act(() => {
        task = result.current.addTask({ title: 'Delete Me' })
      })

      act(() => {
        result.current.deleteTask(task.id)
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      expect(stored).toBeDefined()

      const parsed = JSON.parse(stored!)
      expect(parsed.tasks).toHaveLength(0)
    })
  })

  describe('filterTasks', () => {
    it('should filter tasks by status', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useTasks())

      let task1: any = null
      let task2: any = null
      let task3: any = null

      act(() => {
        task1 = result.current.addTask({ title: 'Task 1' })
      })
      act(() => {
        task2 = result.current.addTask({ title: 'Task 2' })
      })
      act(() => {
        task3 = result.current.addTask({ title: 'Task 3' })
      })
      act(() => {
        result.current.updateTaskStatus(task3.id, 'done')
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      const parsed = JSON.parse(stored!)
      const todoTasks = parsed.tasks.filter((t: any) => t.status === 'todo')
      expect(todoTasks).toHaveLength(2)
    })

    it('should filter tasks by assignee', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useTasks())

      let task1: any = null
      let task2: any = null
      let task3: any = null

      act(() => {
        task1 = result.current.addTask({ title: 'Task 1', assignee: 'John' })
      })
      act(() => {
        task2 = result.current.addTask({ title: 'Task 2', assignee: 'Jane' })
      })
      act(() => {
        task3 = result.current.addTask({ title: 'Task 3', assignee: 'John' })
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      const parsed = JSON.parse(stored!)
      const johnTasks = parsed.tasks.filter((t: any) => t.assignee === 'John')
      expect(johnTasks).toHaveLength(2)
    })
  })

  describe('assignees', () => {
    it('should return unique assignees', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useTasks())

      let task1: any = null
      let task2: any = null
      let task3: any = null

      act(() => {
        task1 = result.current.addTask({ title: 'Task 1', assignee: 'John' })
      })
      act(() => {
        task2 = result.current.addTask({ title: 'Task 2', assignee: 'Jane' })
      })
      act(() => {
        task3 = result.current.addTask({ title: 'Task 3', assignee: 'John' })
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      const parsed = JSON.parse(stored!)

      const assignees = [...new Set(parsed.tasks.map((t: any) => t.assignee).filter(Boolean))]
      expect(assignees.length).toBe(2)
      expect(assignees).toContain('John')
      expect(assignees).toContain('Jane')
    })
  })
})
