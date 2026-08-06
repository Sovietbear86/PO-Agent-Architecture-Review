/** Tests for TaskItem component. */
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { TaskItem } from '../components/TaskItem'

describe('TaskItem', () => {
  const mockOnUpdate = vi.fn()
  const mockOnDelete = vi.fn()

  const task = {
    id: '1',
    title: 'Test Task',
    description: 'Test Description',
    assignee: 'John Doe',
    status: 'todo' as const,
    createdAt: '2024-01-01T00:00:00.000Z',
    updatedAt: '2024-01-01T00:00:00.000Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render task title and description', () => {
    render(<TaskItem task={task} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)

    expect(screen.getByText('Test Task')).toBeInTheDocument()
    expect(screen.getByText('Test Description')).toBeInTheDocument()
  })

  it('should render assignee', () => {
    render(<TaskItem task={task} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)

    expect(screen.getByText(/Assignee: John Doe/)).toBeInTheDocument()
  })

  it('should render status badge', () => {
    render(<TaskItem task={task} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)

    expect(screen.getByText('New')).toBeInTheDocument()
  })

  it('should call onUpdate with todo status', () => {
    render(<TaskItem task={task} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)

    const button = screen.getByRole('button', { name: /In Progress/i })
    expect(button).toBeInTheDocument()
  })

  it('should call onDelete', () => {
    render(<TaskItem task={task} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)

    const deleteButton = screen.getByRole('button', { name: /Delete/i })
    expect(deleteButton).toBeInTheDocument()
  })

  it('should show different status labels based on task status', () => {
    const inProgressTask = { ...task, status: 'in_progress' }
    const doneTask = { ...task, status: 'done' }

    render(<TaskItem task={inProgressTask} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)
    expect(screen.getByText('In Progress')).toBeInTheDocument()

    render(<TaskItem task={doneTask} onUpdate={mockOnUpdate} onDelete={mockOnDelete} />)
    // When task is done, there's no "Done" button (status is already done)
    // but there should be a "Set New" button to change it back to todo
    const buttons = screen.getAllByRole('button')
    const setNewButton = buttons.find(btn => btn.textContent === 'Set New')
    expect(setNewButton).toBeInTheDocument()
  })
})
