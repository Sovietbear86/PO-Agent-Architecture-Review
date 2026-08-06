/** Tests for useLocalStorage hook. */
import { renderHook, act } from '@testing-library/react'
import { useLocalStorage } from '../hooks/useLocalStorage'
import { cleanup } from '@testing-library/react'

describe('useLocalStorage', () => {
  const STORAGE_KEY = 'task-tracker'
  
  beforeEach(() => {
    localStorage.clear()
    cleanup()
  })
  
  afterAll(() => {
    localStorage.clear()
  })
  
  it('should load empty tasks from localStorage when empty', () => {
    localStorage.removeItem(STORAGE_KEY)
    
    const { result } = renderHook(() => useLocalStorage())
    
    expect(result.current.tasks).toEqual([])
  })
  
  it('should save tasks to localStorage', () => {
    localStorage.removeItem(STORAGE_KEY)
    
    const { result } = renderHook(() => useLocalStorage())
    
    act(() => {
      result.current.save([])
    })
    
    const stored = localStorage.getItem(STORAGE_KEY)
    expect(stored).toBe(JSON.stringify({ tasks: [] }))
  })
  
  it('should return stored tasks', () => {
    const storedData = { tasks: [{ id: '1', title: 'Test', status: 'todo', createdAt: '2024-01-01T00:00:00.000Z', updatedAt: '2024-01-01T00:00:00.000Z' }] }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(storedData))
    
    const { result } = renderHook(() => useLocalStorage())
    
    expect(result.current.tasks).toEqual(storedData.tasks)
  })
})
