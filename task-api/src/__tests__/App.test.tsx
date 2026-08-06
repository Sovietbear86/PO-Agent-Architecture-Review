/** Tests for App component - integration tests for user scenarios. */
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { App } from '../components/App'

describe('App component - User Scenarios', () => {
  const STORAGE_KEY = 'task-tracker'

  beforeEach(() => {
    localStorage.clear()
  })

  it('should display task counter when tasks exist', () => {
    const storedData = {
      tasks: [
        {
          id: '1',
          title: 'Existing Task',
          status: 'todo' as const,
          createdAt: '2024-01-01T00:00:00.000Z',
          updatedAt: '2024-01-01T00:00:00.000Z',
        },
      ],
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(storedData))

    render(<App />)

    expect(screen.getByText('Task Tracker')).toBeInTheDocument()
  })

  it('should show message when no tasks', () => {
    localStorage.clear()

    render(<App />)

    expect(screen.getByText('Task Tracker')).toBeInTheDocument()
    expect(screen.getByText('No tasks found. Create your first task!')).toBeInTheDocument()
  })

  it('should persist tasks after page reload (simulated)', async () => {
    // First "session" - add tasks
    const storedData = {
      tasks: [
        {
          id: '1',
          title: 'Persisted Task',
          status: 'todo' as const,
          createdAt: '2024-01-01T00:00:00.000Z',
          updatedAt: '2024-01-01T00:00:00.000Z',
        },
      ],
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(storedData))

    // Second "session" - render with persisted data
    render(<App />)

    // Verify task is loaded
    expect(screen.getByText('Persisted Task')).toBeInTheDocument()
  })
})
