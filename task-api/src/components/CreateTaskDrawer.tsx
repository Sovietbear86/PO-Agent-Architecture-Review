import { useState, useEffect } from 'react'
import { CreateTaskInput } from '../types/task'
import { Drawer } from './Drawer'
import { colors, spacing } from '../styles'

interface CreateTaskDrawerProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: CreateTaskInput) => void
}

export function CreateTaskDrawer({ isOpen, onClose, onSubmit }: CreateTaskDrawerProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [assignee, setAssignee] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [error, setError] = useState('')

  // Reset form when drawer opens
  useEffect(() => {
    if (isOpen) {
      setTitle('')
      setDescription('')
      setAssignee('')
      setSourceUrl('')
      setError('')
    }
  }, [isOpen])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!title.trim()) {
      setError('Название обязательно для заполнения')
      return
    }

    if (title.length > 200) {
      setError('Название должно быть не более 200 символов')
      return
    }

    if (description.length > 1000) {
      setError('Описание должно быть не более 1000 символов')
      return
    }

    if (assignee.length > 100) {
      setError('Исполнитель должен быть не более 100 символов')
      return
    }

    if (sourceUrl.length > 500) {
      setError('URL должен быть не более 500 символов')
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
    onClose()
  }

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title="Создать задачу"
      width="520px"
    >
      <form onSubmit={handleSubmit} style={{ marginTop: '-1rem' }}>
        {error && (
          <div style={{
            backgroundColor: '#fee2e2',
            color: '#991b1b',
            padding: '12px',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '14px',
          }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: '24px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '14px',
            fontWeight: 500,
            color: '#20242c',
          }}>
            Название задачи *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              border: '1px solid #d9dee8',
              borderRadius: '6px',
            }}
            placeholder="Введите название задачи"
            maxLength={200}
            autoFocus
          />
          <div style={{
            fontSize: '12px',
            color: '#8a94a6',
            textAlign: 'right',
            marginTop: '4px',
          }}>
            {title.length} / 200
          </div>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '14px',
            fontWeight: 500,
            color: '#20242c',
          }}>
            Описание
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              border: '1px solid #d9dee8',
              borderRadius: '6px',
              minHeight: '100px',
              resize: 'vertical',
            }}
            placeholder="Описание задачи (опционально)"
            maxLength={1000}
          />
          <div style={{
            fontSize: '12px',
            color: '#8a94a6',
            textAlign: 'right',
            marginTop: '4px',
          }}>
            {description.length} / 1000
          </div>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '14px',
            fontWeight: 500,
            color: '#20242c',
          }}>
            Исполнитель
          </label>
          <input
            type="text"
            value={assignee}
            onChange={(e) => setAssignee(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              border: '1px solid #d9dee8',
              borderRadius: '6px',
            }}
            placeholder="Имя исполнителя (опционально)"
            maxLength={100}
          />
          <div style={{
            fontSize: '12px',
            color: '#8a94a6',
            textAlign: 'right',
            marginTop: '4px',
          }}>
            {assignee.length} / 100
          </div>
        </div>

        <div style={{ marginBottom: '24px' }}>
          <label style={{
            display: 'block',
            marginBottom: '8px',
            fontSize: '14px',
            fontWeight: 500,
            color: '#20242c',
          }}>
            Source URL (SWTR)
          </label>
          <input
            type="text"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              fontSize: '14px',
              border: '1px solid #d9dee8',
              borderRadius: '6px',
            }}
            placeholder="https://portal.works.prod.sbt/swtr/units/all/unit/WMB-XXXXX"
            maxLength={500}
          />
          <div style={{
            fontSize: '12px',
            color: '#8a94a6',
            marginTop: '4px',
          }}>
            Ссылка на задачу в SWTR (опционально)
          </div>
        </div>

        <div style={{
          display: 'flex',
          gap: '12px',
          justifyContent: 'flex-end',
          paddingTop: '24px',
          borderTop: `1px solid ${colors.borderSoft}`,
        }}>
          <button
            type="button"
            onClick={onClose}
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: 500,
              backgroundColor: '#ffffff',
              color: '#20242c',
              border: '1px solid #d9dee8',
            }}
          >
            Отмена
          </button>
          <button
            type="submit"
            style={{
              padding: '10px 20px',
              fontSize: '14px',
              fontWeight: 500,
              backgroundColor: '#315fa8',
              color: '#ffffff',
            }}
          >
            Создать задачу
          </button>
        </div>
      </form>
    </Drawer>
  )
}

export default CreateTaskDrawer
