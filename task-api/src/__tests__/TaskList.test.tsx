/** Tests for TaskList component. */
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { TaskList } from '../components/TaskList'

describe('TaskList', () => {
  const mockOnUpdate = vi.fn()
  const mockOnDelete = vi.fn()

  const tasks = [
    {
      id: '1',
      title: 'Task 1',
      status: 'todo' as const,
      createdAt: '2024-01-01T00:00:00.000Z',
      updatedAt: '2024-01-01T00:00:00.000Z',
    },
    {
      id: '2',
      title: 'Task 2',
      status: 'in_progress' as const,
      createdAt: '2024-01-01T00:00:00.000Z',
      updatedAt: '2024-01-01T00:00:00.000Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render all tasks', () => {
    render(<TaskList tasks={tasks} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)

    expect(screen.getByText('Task 1')).toBeInTheDocument()
    expect(screen.getByText('Task 2')).toBeInTheDocument()
  })

  it('should render no tasks message when empty', () => {
    render(<TaskList tasks={[]} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)

    expect(screen.getByText('No tasks found. Create your first task!')).toBeInTheDocument()
  })

  it('should call onUpdate when Done button clicked', () => {
    render(<TaskList tasks={tasks} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)

    // Get all Done buttons
    const doneButtons = screen.getAllByRole('button', { name: /Done/i })
    // Both tasks have Done buttons since neither is 'done'
    expect(doneButtons).toHaveLength(2)
    
    // Click the Done button on Task 1
    fireEvent.click(doneButtons[0])

    expect(mockOnUpdate).toHaveBeenCalledWith('1', 'done')
  })

  it('should call onDelete for each task', () => {
    render(<TaskList tasks={tasks} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)

    const deleteButtons = screen.getAllByRole('button', { name: /Delete/i })
    expect(deleteButtons).toHaveLength(2)

    fireEvent.click(deleteButtons[0])
    expect(mockOnDelete).toHaveBeenCalledWith('1')
  })
})
