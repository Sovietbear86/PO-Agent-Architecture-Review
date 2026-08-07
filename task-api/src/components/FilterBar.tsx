import { Status } from '../types/task'
import { statusColors, spaceColors, colors } from '../styles/statusColors'
import allStatuses from './statusList'

interface FilterBarProps {
  status: Status | 'all' | string | string[]
  onStatusChange: (status: Status | 'all' | string | string[]) => void
  assignee: string | string[]
  onAssigneeChange: (assignee: string | string[]) => void
  assignees: string[]
  sprint: string | string[]
  onSprintChange: (sprint: string | string[]) => void
  sprints: string[]
  space: string | string[]
  onSpaceChange: (space: string | string[]) => void
  spaces: string[]
}

export function FilterBar({
  status,
  onStatusChange,
  assignee,
  onAssigneeChange,
  assignees,
  sprint,
  onSprintChange,
  sprints,
  space,
  onSpaceChange,
  spaces,
}: FilterBarProps) {
  // Status multi-select logic
  const isAllStatus = status === 'all' || status === '' || (Array.isArray(status) && status.length === 0)
  const selectedStatuses = Array.isArray(status) ? status : (status === 'all' || status === '' ? [] : [status])

  const toggleStatus = (value: string) => {
    if (selectedStatuses.includes(value)) {
      const newStatuses = selectedStatuses.filter(s => s !== value)
      onStatusChange(newStatuses.length > 0 ? newStatuses : 'all')
    } else {
      onStatusChange([...selectedStatuses, value])
    }
  }

  const toggleAllStatus = () => {
    if (isAllStatus || selectedStatuses.length > 0) {
      onStatusChange('all')
    } else {
      onStatusChange([])
    }
  }

  // Assignee multi-select logic
  const isAllAssignees = assignee === 'all' || assignee === '' || (Array.isArray(assignee) && assignee.length === 0)
  const selectedAssignees = Array.isArray(assignee) ? assignee : (assignee === 'all' || assignee === '' ? [] : [assignee])

  const toggleAssignee = (value: string) => {
    if (selectedAssignees.includes(value)) {
      const newAssignees = selectedAssignees.filter(a => a !== value)
      onAssigneeChange(newAssignees.length > 0 ? newAssignees : 'all')
    } else {
      onAssigneeChange([...selectedAssignees, value])
    }
  }

  const toggleAllAssignees = () => {
    if (isAllAssignees || selectedAssignees.length > 0) {
      onAssigneeChange('all')
    } else {
      onAssigneeChange([])
    }
  }

  // Space multi-select logic
  const isAllSpace = space === 'all' || space === '' || (Array.isArray(space) && space.length === 0)
  const selectedSpaces = Array.isArray(space) ? space : (space === 'all' || space === '' ? [] : [space])

  const toggleSpace = (value: string) => {
    if (selectedSpaces.includes(value)) {
      const newSpaces = selectedSpaces.filter(s => s !== value)
      onSpaceChange(newSpaces.length > 0 ? newSpaces : 'all')
    } else {
      onSpaceChange([...selectedSpaces, value])
    }
  }

  const toggleAllSpace = () => {
    if (isAllSpace || selectedSpaces.length > 0) {
      onSpaceChange('all')
    } else {
      onSpaceChange([])
    }
  }

  // Sprint multi-select logic
  const isAllSprints = sprint === 'all' || sprint === '' || (Array.isArray(sprint) && sprint.length === 0)
  const selectedSprints = Array.isArray(sprint) ? sprint : (sprint === 'all' || sprint === '' ? [] : [sprint])

  const toggleSprint = (value: string) => {
    if (selectedSprints.includes(value)) {
      const newSprints = selectedSprints.filter(s => s !== value)
      onSprintChange(newSprints.length > 0 ? newSprints : 'all')
    } else {
      onSprintChange([...selectedSprints, value])
    }
  }

  const toggleAllSprints = () => {
    if (isAllSprints || selectedSprints.length > 0) {
      onSprintChange('all')
    } else {
      onSprintChange([])
    }
  }

  return (
    <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'flex-start', flexWrap: 'wrap' }}>
      {/* Status Filter */}
      <div style={{ minWidth: '200px' }}>
        <label>Status (multi-select):</label>
        <div style={{ marginTop: '0.25rem' }}>
          <button
            onClick={toggleAllStatus}
            style={{
              padding: '0.25rem 0.5rem',
              marginRight: '0.5rem',
              backgroundColor: isAllStatus || selectedStatuses.length === 0 ? colors.accentPrimary : '#fff',
              color: isAllStatus || selectedStatuses.length === 0 ? '#fff' : '#333',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            All
          </button>
          <select
            value=""
            onChange={(e) => {
              if (e.target.value) {
                toggleStatus(e.target.value)
                e.target.selectedIndex = 0
              }
            }}
            style={{
              padding: '0.25rem 0.5rem',
              minWidth: '150px',
              backgroundColor: '#fff',
              border: '1px solid #ddd',
              borderRadius: '4px',
            }}
          >
            <option value="" disabled>
              + Add status...
            </option>
            {allStatuses.map((s) => {
              const isSelected = selectedStatuses.includes(s.value) ||
                s.aliases?.some(a => selectedStatuses.includes(a))
              if (!isSelected) {
                return <option key={s.value} value={s.value}>{s.label}</option>
              }
              return null
            })}
          </select>
        </div>
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
          {selectedStatuses.length === 0 && !isAllStatus && (
            <span style={{ fontSize: '0.8rem', color: '#888' }}>No filter</span>
          )}
          {isAllStatus && <span style={{ fontSize: '0.8rem', color: colors.accentPrimary }}>All statuses</span>}
          {!isAllStatus && selectedStatuses.length > 0 && selectedStatuses.map((s) => {
            const statusInfo = allStatuses.find(st => st.value === s || st.aliases?.includes(s))
            const label = statusInfo ? statusInfo.label : s
            return (
              <span
                key={s}
                onClick={() => toggleStatus(s)}
                style={{
                  padding: '0.15rem 0.4rem',
                  backgroundColor: statusColors[s] || '#999',
                  color: '#fff',
                  borderRadius: '3px',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                }}
                title="Click to remove"
              >
                {label}
              </span>
            )
          })}
        </div>
      </div>

      {/* Space Filter */}
      <div style={{ minWidth: '200px' }}>
        <label>Пространство (multi-select):</label>
        <div style={{ marginTop: '0.25rem' }}>
          <button
            onClick={toggleAllSpace}
            style={{
              padding: '0.25rem 0.5rem',
              marginRight: '0.5rem',
              backgroundColor: isAllSpace || selectedSpaces.length === 0 ? colors.accentPrimary : '#fff',
              color: isAllSpace || selectedSpaces.length === 0 ? '#fff' : '#333',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            All
          </button>
          <select
            value=""
            onChange={(e) => {
              if (e.target.value) {
                toggleSpace(e.target.value)
                e.target.selectedIndex = 0
              }
            }}
            style={{
              padding: '0.25rem 0.5rem',
              minWidth: '150px',
              backgroundColor: '#fff',
              border: '1px solid #ddd',
              borderRadius: '4px',
            }}
          >
            <option value="" disabled>
              + Add space...
            </option>
            {spaces.map((space) => {
              const isSelected = selectedSpaces.includes(space)
              if (!isSelected) {
                return <option key={space} value={space}>{space}</option>
              }
              return null
            })}
          </select>
        </div>
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
          {selectedSpaces.length === 0 && !isAllSpace && (
            <span style={{ fontSize: '0.8rem', color: '#888' }}>No filter</span>
          )}
          {isAllSpace && <span style={{ fontSize: '0.8rem', color: colors.accentPrimary }}>All spaces</span>}
          {!isAllSpace && selectedSpaces.length > 0 && selectedSpaces.map((s) => (
            <span
              key={s}
              onClick={() => toggleSpace(s)}
              style={{
                padding: '0.15rem 0.4rem',
                backgroundColor: spaceColors[s] || '#999',
                color: '#fff',
                borderRadius: '3px',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
              title="Click to remove"
            >
              {s}
            </span>
          ))}
        </div>
      </div>

      {/* Assignee Filter */}
      <div style={{ minWidth: '200px' }}>
        <label>Assignee (multi-select):</label>
        <div style={{ marginTop: '0.25rem' }}>
          <button
            onClick={toggleAllAssignees}
            style={{
              padding: '0.25rem 0.5rem',
              marginRight: '0.5rem',
              backgroundColor: isAllAssignees || selectedAssignees.length === 0 ? colors.accentPrimary : '#fff',
              color: isAllAssignees || selectedAssignees.length === 0 ? '#fff' : '#333',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            All
          </button>
          <select
            value=""
            onChange={(e) => {
              if (e.target.value) {
                toggleAssignee(e.target.value)
                e.target.selectedIndex = 0
              }
            }}
            style={{
              padding: '0.25rem 0.5rem',
              minWidth: '150px',
              backgroundColor: '#fff',
              border: '1px solid #ddd',
              borderRadius: '4px',
            }}
          >
            <option value="" disabled>
              + Add assignee...
            </option>
            {assignees.map((assignee) => {
              const isSelected = selectedAssignees.includes(assignee)
              if (!isSelected) {
                return <option key={assignee} value={assignee}>{assignee}</option>
              }
              return null
            })}
          </select>
        </div>
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
          {selectedAssignees.length === 0 && !isAllAssignees && (
            <span style={{ fontSize: '0.8rem', color: '#888' }}>No filter</span>
          )}
          {isAllAssignees && <span style={{ fontSize: '0.8rem', color: colors.accentPrimary }}>All assignees</span>}
          {!isAllAssignees && selectedAssignees.length > 0 && selectedAssignees.map((a) => (
            <span
              key={a}
              onClick={() => toggleAssignee(a)}
              style={{
                padding: '0.15rem 0.4rem',
                backgroundColor: colors.accentPrimary,
                color: '#fff',
                borderRadius: '3px',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
              title="Click to remove"
            >
              {a}
            </span>
          ))}
        </div>
      </div>

      {/* Sprint Filter */}
      <div style={{ minWidth: '200px' }}>
        <label>Sprint (multi-select):</label>
        <div style={{ marginTop: '0.25rem' }}>
          <button
            onClick={toggleAllSprints}
            style={{
              padding: '0.25rem 0.5rem',
              marginRight: '0.5rem',
              backgroundColor: isAllSprints || selectedSprints.length === 0 ? colors.accentPrimary : '#fff',
              color: isAllSprints || selectedSprints.length === 0 ? '#fff' : '#333',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            All
          </button>
          <select
            value=""
            onChange={(e) => {
              if (e.target.value) {
                toggleSprint(e.target.value)
                e.target.selectedIndex = 0
              }
            }}
            style={{
              padding: '0.25rem 0.5rem',
              minWidth: '150px',
              backgroundColor: '#fff',
              border: '1px solid #ddd',
              borderRadius: '4px',
            }}
          >
            <option value="" disabled>
              + Add sprint...
            </option>
            <option value="NONE">NONE (без спринта)</option>
            {sprints.map((sprint) => {
              const isSelected = selectedSprints.includes(sprint)
              if (!isSelected) {
                return <option key={sprint} value={sprint}>{sprint}</option>
              }
              return null
            })}
          </select>
        </div>
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
          {selectedSprints.length === 0 && !isAllSprints && (
            <span style={{ fontSize: '0.8rem', color: '#888' }}>No filter</span>
          )}
          {isAllSprints && <span style={{ fontSize: '0.8rem', color: colors.accentPrimary }}>All sprints</span>}
          {!isAllSprints && selectedSprints.length > 0 && selectedSprints.map((s) => (
            <span
              key={s}
              onClick={() => toggleSprint(s)}
              style={{
                padding: '0.15rem 0.4rem',
                backgroundColor: colors.accentPrimary,
                color: '#fff',
                borderRadius: '3px',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
              title="Click to remove"
            >
              {s}
            </span>
          ))}
        </div>
      </div>

      {/* Space Filter */}
      <div style={{ minWidth: '200px' }}>
        <label>Пространство (multi-select):</label>
        <div style={{ marginTop: '0.25rem' }}>
          <button
            onClick={toggleAllSpace}
            style={{
              padding: '0.25rem 0.5rem',
              marginRight: '0.5rem',
              backgroundColor: isAllSpace || selectedSpaces.length === 0 ? colors.accentPrimary : '#fff',
              color: isAllSpace || selectedSpaces.length === 0 ? '#fff' : '#333',
              border: '1px solid #ddd',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            All
          </button>
          <select
            value=""
            onChange={(e) => {
              if (e.target.value) {
                toggleSpace(e.target.value)
                e.target.selectedIndex = 0
              }
            }}
            style={{
              padding: '0.25rem 0.5rem',
              minWidth: '150px',
              backgroundColor: '#fff',
              border: '1px solid #ddd',
              borderRadius: '4px',
            }}
          >
            <option value="" disabled>
              + Add space...
            </option>
            {spaces.map((space) => {
              const isSelected = selectedSpaces.includes(space)
              if (!isSelected) {
                return <option key={space} value={space}>{space}</option>
              }
              return null
            })}
          </select>
        </div>
        <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
          {selectedSpaces.length === 0 && !isAllSpace && (
            <span style={{ fontSize: '0.8rem', color: '#888' }}>No filter</span>
          )}
          {isAllSpace && <span style={{ fontSize: '0.8rem', color: colors.accentPrimary }}>All spaces</span>}
          {!isAllSpace && selectedSpaces.length > 0 && selectedSpaces.map((s) => (
            <span
              key={s}
              onClick={() => toggleSpace(s)}
              style={{
                padding: '0.15rem 0.4rem',
                backgroundColor: spaceColors[s] || '#999',
                color: '#fff',
                borderRadius: '3px',
                fontSize: '0.8rem',
                cursor: 'pointer',
              }}
              title="Click to remove"
            >
              {s}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
