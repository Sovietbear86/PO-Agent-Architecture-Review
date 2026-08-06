/** Tests for TaskForm component. */
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { TaskForm } from '../components/TaskForm'

describe('TaskForm', () => {
  const mockOnSubmit = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render form fields', () => {
    render(<TaskForm onSubmit={mockOnSubmit} />)

    expect(screen.getByPlaceholderText('Task title')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Task description')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Assignee name')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create Task/i })).toBeInTheDocument()
  })

  it('should call onSubmit with valid data', () => {
    render(<TaskForm onSubmit={mockOnSubmit} />)

    const titleInput = screen.getByPlaceholderText('Task title')
    const descInput = screen.getByPlaceholderText('Task description')
    const assigneeInput = screen.getByPlaceholderText('Assignee name')
    const submitButton = screen.getByRole('button', { name: /Create Task/i })

    fireEvent.change(titleInput, { target: { value: 'Test Task' } })
    fireEvent.change(descInput, { target: { value: 'Test Description' } })
    fireEvent.change(assigneeInput, { target: { value: 'John Doe' } })
    fireEvent.click(submitButton)

    expect(mockOnSubmit).toHaveBeenCalledWith({
      title: 'Test Task',
      description: 'Test Description',
      assignee: 'John Doe',
    })
  })

  it('should not submit with empty title', () => {
    render(<TaskForm onSubmit={mockOnSubmit} />)

    const submitButton = screen.getByRole('button', { name: /Create Task/i })
    fireEvent.click(submitButton)

    expect(mockOnSubmit).not.toHaveBeenCalled()
    expect(screen.getByText('Title is required')).toBeInTheDocument()
  })

  it('should limit title to 200 characters', () => {
    render(<TaskForm onSubmit={mockOnSubmit} />)

    const titleInput = screen.getByPlaceholderText('Task title')
    const longTitle = 'A'.repeat(201)
    fireEvent.change(titleInput, { target: { value: longTitle } })

    expect(titleInput).toHaveAttribute('maxLength', '200')
  })

  it('should limit description to 1000 characters', () => {
    render(<TaskForm onSubmit={mockOnSubmit} />)

    const descInput = screen.getByPlaceholderText('Task description')
    expect(descInput).toHaveAttribute('maxLength', '1000')
  })

  it('should limit assignee to 100 characters', () => {
    render(<TaskForm onSubmit={mockOnSubmit} />)

    const assigneeInput = screen.getByPlaceholderText('Assignee name')
    expect(assigneeInput).toHaveAttribute('maxLength', '100')
  })
})
