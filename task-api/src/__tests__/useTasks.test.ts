/** Tests for useTasks hook. */
import { renderHook, act, waitFor } from '@testing-library/react'
import { useTasks } from '../hooks/useTasks'
import { cleanup } from '@testing-library/react'

describe('useTasks', () => {
  const STORAGE_KEY = 'task-tracker'

  beforeEach(() => {
    localStorage.clear()
    cleanup()
  })

  afterAll(() => {
    localStorage.clear()
  })

  it('should add a new task', async () => {
    const { result } = renderHook(() => useTasks())

    await act(async () => {
      await result.current.addTask({ title: 'Test Task' })
    })

    // Wait for task to be added to state
    await waitFor(() => {
      expect(result.current.tasks.length).toBe(1)
      expect(result.current.tasks[0].title).toBe('Test Task')
    })
  })

  it('should update a task status', async () => {
    const { result } = renderHook(() => useTasks())

    // Add task
    await act(async () => {
      await result.current.addTask({ title: 'Test Task' })
    })

    // Wait for task to be in state
    await waitFor(() => {
      expect(result.current.tasks.length).toBe(1)
    })

    // Update status
    await act(async () => {
      await result.current.updateTaskStatus(result.current.tasks[0].id, 'in_progress')
    })

    // Wait for status to update
    await waitFor(() => {
      expect(result.current.tasks[0].status).toBe('in_progress')
    })
  })

  it('should delete a task', async () => {
    const { result } = renderHook(() => useTasks())

    // Add task
    await act(async () => {
      await result.current.addTask({ title: 'Test Task' })
    })

    // Wait for task to be in state
    await waitFor(() => {
      expect(result.current.tasks.length).toBe(1)
    })

    // Delete task
    await act(async () => {
      const deleted = await result.current.deleteTask(result.current.tasks[0].id)
      expect(deleted).toBe(true)
    })

    // Wait for task to be removed
    await waitFor(() => {
      expect(result.current.tasks.length).toBe(0)
    })
  })

  it('should filter tasks by status', async () => {
    const { result } = renderHook(() => useTasks())

    // Add tasks
    await act(async () => {
      await result.current.addTask({ title: 'Task 1' })
    })
    await act(async () => {
      await result.current.addTask({ title: 'Task 2' })
    })
    await act(async () => {
      await result.current.addTask({ title: 'Task 3' })
    })

    // Wait for tasks to be in state
    await waitFor(() => {
      expect(result.current.tasks.length).toBe(3)
    })

    // Update status of task 3
    await act(async () => {
      await result.current.updateTaskStatus(result.current.tasks[2].id, 'done')
    })

    // Wait for status to update
    await waitFor(() => {
      const filtered = result.current.filterTasks({ status: 'todo' })
      expect(filtered.length).toBe(2)
    })
  })

  it('should filter tasks by assignee', async () => {
    const { result } = renderHook(() => useTasks())

    // Add tasks
    await act(async () => {
      await result.current.addTask({ title: 'Task 1', assignee: 'John' })
    })
    await act(async () => {
      await result.current.addTask({ title: 'Task 2', assignee: 'Jane' })
    })
    await act(async () => {
      await result.current.addTask({ title: 'Task 3', assignee: 'John' })
    })

    // Wait for tasks to be in state
    await waitFor(() => {
      expect(result.current.tasks.length).toBe(3)
    })

    // Filter by assignee
    await waitFor(() => {
      const filtered = result.current.filterTasks({ assignee: 'John' })
      expect(filtered.length).toBe(2)
    })
  })

  it('should return unique assignees', async () => {
    const { result } = renderHook(() => useTasks())

    // Add tasks
    await act(async () => {
      await result.current.addTask({ title: 'Task 1', assignee: 'John' })
    })
    await act(async () => {
      await result.current.addTask({ title: 'Task 2', assignee: 'Jane' })
    })
    await act(async () => {
      await result.current.addTask({ title: 'Task 3', assignee: 'John' })
    })

    // Wait for tasks to be in state
    await waitFor(() => {
      expect(result.current.tasks.length).toBe(3)
    })

    // Check assignees
    await waitFor(() => {
      const assignees = result.current.assignees
      expect(assignees.length).toBe(2)
      expect(assignees).toContain('John')
      expect(assignees).toContain('Jane')
    })
  })
})
