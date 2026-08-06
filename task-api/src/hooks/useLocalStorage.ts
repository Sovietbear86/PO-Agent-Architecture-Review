import { useEffect, useState } from 'react'
import { StorageData } from '../types/localStorage'
import { Task } from '../types/task'

const STORAGE_KEY = 'task-tracker'

/** Load tasks from localStorage. */
export function loadTasks(): StorageData {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('Failed to load tasks from localStorage:', error)
  }
  return { tasks: [] }
}

/** Save tasks to localStorage. */
export function saveTasks(data: StorageData): boolean {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    return true
  } catch (error) {
    console.error('Failed to save tasks to localStorage:', error)
    return false
  }
}

/** Hook for managing localStorage operations. */
export function useLocalStorage() {
  const [data, setData] = useState<StorageData>(() => loadTasks())

  useEffect(() => {
    // First try to load from localStorage
    const stored = loadTasks()
    if (stored.tasks.length > 0) {
      setData(stored)
    }
  }, [])

  const save = (tasks: Task[]) => {
    const newData: StorageData = { tasks }
    const success = saveTasks(newData)
    if (success) {
      setData(newData)
    }
    return success
  }

  return {
    tasks: data.tasks,
    save,
  }
}
