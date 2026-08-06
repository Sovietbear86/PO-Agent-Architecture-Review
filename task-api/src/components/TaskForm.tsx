import { useState } from 'react'
import { CreateTaskInput } from '../types/task'

interface TaskFormProps {
  onSubmit: (data: CreateTaskInput) => void
}

export function TaskForm({ onSubmit }: TaskFormProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [assignee, setAssignee] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!title.trim()) {
      setError('Title is required')
      return
    }

    if (title.length > 200) {
      setError('Title must be 200 characters or less')
      return
    }

    if (description.length > 1000) {
      setError('Description must be 1000 characters or less')
      return
    }

    if (assignee.length > 100) {
      setError('Assignee must be 100 characters or less')
      return
    }

    if (sourceUrl.length > 500) {
      setError('Source URL must be 500 characters or less')
      return
    }

    onSubmit({ 
      title: title.trim(), 
      description: description.trim() || undefined, 
      assignee: assignee.trim() || undefined,
      sourceUrl: sourceUrl.trim() || undefined
    })
    setTitle('')
    setDescription('')
    setAssignee('')
    setSourceUrl('')
  }

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: '1rem', padding: '1rem', border: '1px solid #ccc', borderRadius: '4px' }}>
      <h3>Create Task</h3>

      {error && <div style={{ color: 'red', marginBottom: '0.5rem' }}>{error}</div>}

      <div style={{ marginBottom: '0.5rem' }}>
        <label>
          Title:
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={{ marginLeft: '0.5rem', width: '200px' }}
            placeholder="Task title"
            maxLength={200}
          />
        </label>
      </div>

      <div style={{ marginBottom: '0.5rem' }}>
        <label>
          Description:
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={{ marginLeft: '0.5rem', width: '200px', height: '60px' }}
            placeholder="Task description"
            maxLength={1000}
          />
        </label>
      </div>

      <div style={{ marginBottom: '0.5rem' }}>
        <label>
          Assignee:
          <input
            type="text"
            value={assignee}
            onChange={(e) => setAssignee(e.target.value)}
            style={{ marginLeft: '0.5rem', width: '150px' }}
            placeholder="Assignee name"
            maxLength={100}
          />
        </label>
      </div>

      <div style={{ marginBottom: '0.5rem' }}>
        <label>
          Source URL:
          <input
            type="text"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
            style={{ marginLeft: '0.5rem', width: '300px' }}
            placeholder="https://portal.works.prod.sbt/swtr/units/all/unit/WMB-29890"
            maxLength={500}
          />
        </label>
      </div>

      <button type="submit" style={{ padding: '0.5rem 1rem' }}>Create Task</button>
    </form>
  )
}
