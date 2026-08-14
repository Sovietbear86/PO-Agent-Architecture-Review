import { useState, useEffect } from 'react'
import { api, team as teamApi } from '../api'
import { AppShell, Sidebar, SidebarItem, TopBar, TaskList } from '../components'
import type { Sprint, TeamMember } from '../types'

export function SprintView() {
  const [sprints, setSprints] = useState<Sprint[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'list' | 'metrics'>('list')

  useEffect(() => {
    const loadSprints = async () => {
      try {
        const response = await api.get('/sprints')
        setSprints(response.data)
      } catch (error) {
        console.error('Failed to load sprints:', error)
      } finally {
        setLoading(false)
      }
    }
    loadSprints()
  }, [])

  if (loading) return <div className="p-4">Loading...</div>

  return (
    <Layout
      sidebar={
        <Sidebar>
          <SidebarItem label="Обзор" onClick={() => window.location.href = '/'} />
          <SidebarItem label="Задачи" onClick={() => window.location.href = '/tasks'} />
          <SidebarItem label="Спринты" active />
          <SidebarItem label="Релизы" onClick={() => window.location.href = '/releases'} />
          <SidebarItem label="Команда" onClick={() => window.location.href = '/team'} />
          <SidebarItem label="Аналитика" onClick={() => window.location.href = '/quality'} />
          <SidebarItem label="История" onClick={() => window.location.href = '/history'} />
        </Sidebar>
      }
      content={
        <div style={{ flex: 1 }}>
          <TopBar
            title="Спринты"
            subtitle="Управление спринтами и задачами"
            rightContent={null}
          />

          <div style={{ marginTop: '1rem' }}>
            {sprints.map((sprint) => (
              <div key={sprint.id} style={{
                backgroundColor: '#ffffff',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(27, 39, 61, 0.08)',
                padding: '24px',
                marginBottom: '24px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#20242c', margin: '0 0 8px' }}>
                      {sprint.name}
                    </h2>
                    <p style={{ fontSize: '14px', color: '#667085', margin: 0 }}>{sprint.id}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '14px', color: '#667085', margin: '0 0 8px' }}>
                      {sprint.start_date} - {sprint.end_date}
                    </p>
                  </div>
                </div>
                {sprint.goal && (
                  <p style={{ fontSize: '14px', color: '#20242c', marginBottom: '16px', lineHeight: '1.5' }}>
                    {sprint.goal}
                  </p>
                )}
                {sprint.tasks.length > 0 && (
                  <div>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, color: '#20242c', marginBottom: '16px' }}>
                      Задачи ({sprint.tasks.length})
                    </h3>
                    <TaskList tasks={sprint.tasks} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      }
    />
  )
}

export default SprintView
