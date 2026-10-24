import { useState, useEffect } from 'react'
import { api, team as teamApi } from '../api'
import { AppShell, Sidebar, SidebarItem, TopBar } from '../components'
import type { TeamMember } from '../types'

export function TeamView() {
  const [members, setMembers] = useState<TeamMember[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'members' | 'capacity'>('members')

  useEffect(() => {
    const loadTeam = async () => {
      try {
        const response = await teamApi.getMembers()
        setMembers(response.data)
      } catch (error) {
        console.error('Failed to load team:', error)
      } finally {
        setLoading(false)
      }
    }
    loadTeam()
  }, [])

  if (loading) return <div className="p-4">Loading...</div>

  const totalCapacity = members.reduce((sum, m) => sum + m.capacity_hours, 0)

  return (
    <Layout
      sidebar={
        <Sidebar>
          <SidebarItem label="Обзор" onClick={() => window.location.href = '/'} />
          <SidebarItem label="Задачи" onClick={() => window.location.href = '/tasks'} />
          <SidebarItem label="Спринты" onClick={() => window.location.href = '/sprint'} />
          <SidebarItem label="Релизы" onClick={() => window.location.href = '/releases'} />
          <SidebarItem label="Команда" active />
          <SidebarItem label="Аналитика" onClick={() => window.location.href = '/quality'} />
          <SidebarItem label="История" onClick={() => window.location.href = '/history'} />
        </Sidebar>
      }
      content={
        <div style={{ flex: 1 }}>
          <TopBar
            title="Команда"
            subtitle="Члены команды и их емкость"
            rightContent={null}
          />

          <div style={{ marginTop: '1rem', display: 'flex', gap: '16px', marginBottom: '24px' }}>
            <button
              onClick={() => setActiveTab('members')}
              style={{
                padding: '12px 24px',
                backgroundColor: activeTab === 'members' ? '#315fa8' : '#ffffff',
                color: activeTab === 'members' ? '#ffffff' : '#20242c',
                border: `1px solid ${activeTab === 'members' ? '#315fa8' : '#d9dee8'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              Члены команды
            </button>
            <button
              onClick={() => setActiveTab('capacity')}
              style={{
                padding: '12px 24px',
                backgroundColor: activeTab === 'capacity' ? '#315fa8' : '#ffffff',
                color: activeTab === 'capacity' ? '#ffffff' : '#20242c',
                border: `1px solid ${activeTab === 'capacity' ? '#315fa8' : '#d9dee8'}`,
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              Емкость
            </button>
          </div>

          {activeTab === 'members' ? (
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(27, 39, 61, 0.08)',
              overflow: 'hidden',
            }}>
              <table style={{ width: '100%' }}>
                <thead style={{ backgroundColor: '#f5f7fa' }}>
                  <tr>
                    <th style={{ padding: '16px', textAlign: 'left', fontSize: '14px', fontWeight: 600, color: '#20242c' }}>
                      Имя
                    </th>
                    <th style={{ padding: '16px', textAlign: 'left', fontSize: '14px', fontWeight: 600, color: '#20242c' }}>
                      Логин
                    </th>
                    <th style={{ padding: '16px', textAlign: 'left', fontSize: '14px', fontWeight: 600, color: '#20242c' }}>
                      Роль
                    </th>
                    <th style={{ padding: '16px', textAlign: 'left', fontSize: '14px', fontWeight: 600, color: '#20242c' }}>
                      Навыки
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((member) => (
                    <tr key={member.login} style={{ borderBottom: '1px solid #e9edf3' }}>
                      <td style={{ padding: '16px', fontSize: '14px', color: '#20242c' }}>{member.name}</td>
                      <td style={{ padding: '16px', fontSize: '14px', fontFamily: 'monospace', color: '#667085' }}>
                        {member.login}
                      </td>
                      <td style={{ padding: '16px', fontSize: '14px', color: '#20242c' }}>{member.role}</td>
                      <td style={{ padding: '16px' }}>
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          {member.skills.map((skill) => (
                            <span
                              key={skill}
                              style={{
                                padding: '4px 12px',
                                backgroundColor: '#e8f0fd',
                                color: '#315fa8',
                                borderRadius: '4px',
                                fontSize: '12px',
                                fontWeight: 500,
                              }}
                            >
                              {skill}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(27, 39, 61, 0.08)',
              padding: '32px',
            }}>
              <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#20242c', margin: '0 0 24px' }}>
                Общая емкость команды
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px' }}>
                <div style={{
                  padding: '24px',
                  backgroundColor: '#e8f0fd',
                  borderRadius: '12px',
                  textAlign: 'center',
                }}>
                  <p style={{ fontSize: '32px', fontWeight: 700, color: '#315fa8', margin: '0 0 8px' }}>
                    {totalCapacity}ч
                  </p>
                  <p style={{ fontSize: '14px', color: '#667085', margin: 0 }}>
                    Еженедельная емкость
                  </p>
                </div>
                <div style={{
                  padding: '24px',
                  backgroundColor: '#e6f4ea',
                  borderRadius: '12px',
                  textAlign: 'center',
                }}>
                  <p style={{ fontSize: '32px', fontWeight: 700, color: '#27ae60', margin: '0 0 8px' }}>
                    {members.length}
                  </p>
                  <p style={{ fontSize: '14px', color: '#667085', margin: 0 }}>
                    Членов команды
                  </p>
                </div>
                <div style={{
                  padding: '24px',
                  backgroundColor: '#f5f7fa',
                  borderRadius: '12px',
                  textAlign: 'center',
                }}>
                  <p style={{ fontSize: '32px', fontWeight: 700, color: '#3498db', margin: '0 0 8px' }}>
                    {Math.round(totalCapacity / 5)}
                  </p>
                  <p style={{ fontSize: '14px', color: '#667085', margin: 0 }}>
                    Человеко-дней
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      }
    />
  )
}

export default TeamView
