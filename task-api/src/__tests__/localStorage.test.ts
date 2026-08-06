/** Tests for localStorage persistence - save and load tasks. */
import { renderHook, act, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { loadTasks, saveTasks, useLocalStorage } from '../hooks/useLocalStorage'

describe('localStorage persistence', () => {
  const STORAGE_KEY = 'task-tracker'

  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('loadTasks', () => {
    it('should return empty array when no data in localStorage', () => {
      localStorage.removeItem(STORAGE_KEY)
      const result = loadTasks()
      expect(result).toEqual({ tasks: [] })
    })

    it('should return tasks from localStorage when data exists', () => {
      const storedData = {
        tasks: [
          {
            id: '1',
            title: 'Test Task',
            status: 'todo',
            createdAt: '2024-01-01T00:00:00.000Z',
            updatedAt: '2024-01-01T00:00:00.000Z',
          },
        ],
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(storedData))

      const result = loadTasks()
      expect(result).toEqual(storedData)
    })

    it('should handle empty localStorage gracefully', () => {
      localStorage.removeItem(STORAGE_KEY)
      const result = loadTasks()
      expect(result.tasks).toHaveLength(0)
    })
  })

  describe('saveTasks', () => {
    it('should save tasks to localStorage', () => {
      const data = { tasks: [{ id: '1', title: 'Task', status: 'todo', createdAt: '2024-01-01T00:00:00.000Z', updatedAt: '2024-01-01T00:00:00.000Z' }] }
      saveTasks(data)

      const stored = localStorage.getItem(STORAGE_KEY)
      expect(stored).toBe(JSON.stringify(data))
    })

    it('should save empty tasks array', () => {
      saveTasks({ tasks: [] })
      const stored = localStorage.getItem(STORAGE_KEY)
      expect(stored).toBe(JSON.stringify({ tasks: [] }))
    })
  })

  describe('useLocalStorage hook', () => {
    it('should initialize with empty tasks', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useLocalStorage())
      expect(result.current.tasks).toEqual([])
    })

    it('should load existing tasks from localStorage', () => {
      const storedData = {
        tasks: [
          {
            id: '1',
            title: 'Existing Task',
            status: 'todo',
            createdAt: '2024-01-01T00:00:00.000Z',
            updatedAt: '2024-01-01T00:00:00.000Z',
          },
        ],
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(storedData))

      const { result } = renderHook(() => useLocalStorage())
      expect(result.current.tasks).toEqual(storedData.tasks)
    })

    it('should save tasks when save is called', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useLocalStorage())

      act(() => {
        result.current.save([])
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      expect(stored).toBe(JSON.stringify({ tasks: [] }))
    })

    it('should persist tasks across multiple save calls', () => {
      localStorage.removeItem(STORAGE_KEY)
      const { result } = renderHook(() => useLocalStorage())

      act(() => {
        result.current.save([
          { id: '1', title: 'Task 1', status: 'todo', createdAt: '2024-01-01T00:00:00.000Z', updatedAt: '2024-01-01T00:00:00.000Z' },
        ])
      })

      act(() => {
        result.current.save([
          { id: '1', title: 'Task 1', status: 'todo', createdAt: '2024-01-01T00:00:00.000Z', updatedAt: '2024-01-01T00:00:00.000Z' },
          { id: '2', title: 'Task 2', status: 'todo', createdAt: '2024-01-01T00:00:00.000Z', updatedAt: '2024-01-01T00:00:00.000Z' },
        ])
      })

      const stored = localStorage.getItem(STORAGE_KEY)
      expect(stored).toBe(JSON.stringify({
        tasks: [
          { id: '1', title: 'Task 1', status: 'todo', createdAt: '2024-01-01T00:00:00.000Z', updatedAt: '2024-01-01T00:00:00.000Z' },
          { id: '2', title: 'Task 2', status: 'todo', createdAt: '2024-01-01T00:00:00.000Z', updatedAt: '2024-01-01T00:00:00.000Z' },
        ],
      }))
    })
  })
})
