import { useState, useEffect } from 'react'
import { api, releases as releaseApi } from '../api'
import { AppShell, Sidebar, SidebarItem, TopBar, TaskList } from '../components'
import type { Release } from '../types'

export function ReleasesView() {
  const [releases, setReleases] = useState<Release[]>([])
  const [loading, setLoading] = useState(true)
  const [expandedRelease, setExpandedRelease] = useState<string | null>(null)

  useEffect(() => {
    const loadReleases = async () => {
      try {
        const response = await releaseApi.getAll()
        setReleases(response.data)
      } catch (error) {
        console.error('Failed to load releases:', error)
      } finally {
        setLoading(false)
      }
    }
    loadReleases()
  }, [])

  if (loading) return <div className="p-4">Loading...</div>

  return (
    <Layout
      sidebar={
        <Sidebar>
          <SidebarItem label="Обзор" onClick={() => window.location.href = '/'} />
          <SidebarItem label="Задачи" onClick={() => window.location.href = '/tasks'} />
          <SidebarItem label="Спринты" onClick={() => window.location.href = '/sprint'} />
          <SidebarItem label="Релизы" active />
          <SidebarItem label="Команда" onClick={() => window.location.href = '/team'} />
          <SidebarItem label="Аналитика" onClick={() => window.location.href = '/quality'} />
          <SidebarItem label="История" onClick={() => window.location.href = '/history'} />
        </Sidebar>
      }
      content={
        <div style={{ flex: 1 }}>
          <TopBar
            title="Релизы"
            subtitle="Управление релизами и фичами"
            rightContent={null}
          />

          <div style={{ marginTop: '1rem' }}>
            {releases.map((release) => (
              <div key={release.id} style={{
                backgroundColor: '#ffffff',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(27, 39, 61, 0.08)',
                padding: '24px',
                marginBottom: '24px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div style={{ flex: 1 }}>
                    <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#20242c', margin: '0 0 8px' }}>
                      {release.name}
                    </h2>
                    <p style={{ fontSize: '14px', color: '#667085', margin: 0 }}>{release.id}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '14px', color: '#667085', margin: '0 0 8px' }}>
                      {release.start_date} - {release.target_date}
                    </p>
                    <span style={{
                      padding: '4px 12px',
                      backgroundColor: release.status === 'active' ? '#e6f4ea' : release.status === 'planned' ? '#e8f0fd' : '#f5f7fa',
                      color: release.status === 'active' ? '#27ae60' : release.status === 'planned' ? '#315fa8' : '#667085',
                      borderRadius: '4px',
                      fontSize: '12px',
                      fontWeight: 600,
                    }}>
                      {release.status === 'active' ? 'Активен' : release.status === 'planned' ? 'Запланирован' : 'Завершен'}
                    </span>
                  </div>
                </div>
                {release.description && (
                  <p style={{ fontSize: '14px', color: '#20242c', marginBottom: '16px', lineHeight: '1.5' }}>
                    {release.description}
                  </p>
                )}
                
                <button
                  onClick={() => setExpandedRelease(expandedRelease === release.id ? null : release.id)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#e8f0fd',
                    color: '#315fa8',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: 500,
                    fontSize: '13px',
                  }}
                >
                  {expandedRelease === release.id ? 'Скрыть задачи' : `Показать задачи (${release.tasks.length})`}
                </button>

                {expandedRelease === release.id && release.tasks.length > 0 && (
                  <div style={{ marginTop: '16px' }}>
                    <TaskList tasks={release.tasks} />
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

export default ReleasesView
