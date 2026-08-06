/** Tests for FilterBar component. */
import { render, screen, fireEvent } from '@testing-library/react'
import { vi } from 'vitest'
import { FilterBar } from '../components/FilterBar'
import { Status } from '../types/task'

describe('FilterBar', () => {
  const mockOnStatusChange = vi.fn()
  const mockOnAssigneeChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render status select with all options', () => {
    render(
      <FilterBar
        status="all"
        onStatusChange={mockOnStatusChange}
        assignee=""
        onAssigneeChange={mockOnAssigneeChange}
        assignees={[]}
      />
    )

    // Get all select elements
    const selects = screen.getAllByRole('combobox')
    expect(selects).toHaveLength(2)

    // First select is status
    const statusSelect = selects[0]
    expect(statusSelect).toBeInTheDocument()

    // Check options are present
    const options = statusSelect.querySelectorAll('option')
    expect(options).toHaveLength(4)
  })

  it('should call onStatusChange when status changes', () => {
    render(
      <FilterBar
        status="todo"
        onStatusChange={mockOnStatusChange}
        assignee=""
        onAssigneeChange={mockOnAssigneeChange}
        assignees={[]}
      />
    )

    const selects = screen.getAllByRole('combobox')
    const statusSelect = selects[0]
    fireEvent.change(statusSelect, { target: { value: 'in_progress' } })

    expect(mockOnStatusChange).toHaveBeenCalledWith('in_progress')
  })

  it('should render assignee select with options', () => {
    render(
      <FilterBar
        status="all"
        onStatusChange={mockOnStatusChange}
        assignee=""
        onAssigneeChange={mockOnAssigneeChange}
        assignees={['John', 'Jane']}
      />
    )

    const selects = screen.getAllByRole('combobox')
    expect(selects).toHaveLength(2)

    // Check assignee options
    const assigneeSelect = selects[1]
    const options = assigneeSelect.querySelectorAll('option')
    expect(options).toHaveLength(3) // 'all' + 2 assignees

    expect(screen.getByText('John')).toBeInTheDocument()
    expect(screen.getByText('Jane')).toBeInTheDocument()
  })

  it('should call onAssigneeChange when assignee changes', () => {
    render(
      <FilterBar
        status="all"
        onStatusChange={mockOnStatusChange}
        assignee="John"
        onAssigneeChange={mockOnAssigneeChange}
        assignees={['John', 'Jane']}
      />
    )

    const selects = screen.getAllByRole('combobox')
    const assigneeSelect = selects[1]
    fireEvent.change(assigneeSelect, { target: { value: 'Jane' } })

    expect(mockOnAssigneeChange).toHaveBeenCalledWith('Jane')
  })
})
