import { useState, useEffect } from 'react'
import { api, quality as qualityApi } from '../api'
import { AppShell, Sidebar, SidebarItem, TopBar } from '../components'
import type { EvaluationResult } from '../types'

export function QualityView() {
  const [results, setResults] = useState<EvaluationResult[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedResult, setSelectedResult] = useState<EvaluationResult | null>(null)

  useEffect(() => {
    const loadResults = async () => {
      try {
        const response = await qualityApi.getEvalResults()
        setResults(response.data)
      } catch (error) {
        console.error('Failed to load eval results:', error)
      } finally {
        setLoading(false)
      }
    }
    loadResults()
  }, [])

  if (loading) return <div className="p-4">Loading...</div>

  const avgScore = results.length
    ? (results.reduce((sum, r) => sum + r.quality_score, 0) / results.length).toFixed(2)
    : 'N/A'

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#27ae60'
    if (score >= 0.6) return '#f39c12'
    return '#c0392b'
  }

  return (
    <Layout
      sidebar={
        <Sidebar>
          <SidebarItem label="Обзор" onClick={() => window.location.href = '/'} />
          <SidebarItem label="Задачи" onClick={() => window.location.href = '/tasks'} />
          <SidebarItem label="Спринты" onClick={() => window.location.href = '/sprint'} />
          <SidebarItem label="Релизы" onClick={() => window.location.href = '/releases'} />
          <SidebarItem label="Команда" onClick={() => window.location.href = '/team'} />
          <SidebarItem label="Аналитика" active />
          <SidebarItem label="История" onClick={() => window.location.href = '/history'} />
        </Sidebar>
      }
      content={
        <div style={{ flex: 1 }}>
          <TopBar
            title="Аналитика и качество"
            subtitle="Оценки качества и метрики"
            rightContent={null}
          />

          <div style={{ marginTop: '1rem' }}>
            <div style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              boxShadow: '0 1px 3px rgba(27, 39, 61, 0.08)',
              padding: '24px',
              marginBottom: '24px',
            }}>
              <h2 style={{ fontSize: '20px', fontWeight: 600, color: '#20242c', margin: '0 0 24px' }}>
                Оценки качества
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px' }}>
                <div style={{
                  padding: '24px',
                  backgroundColor: '#e8f0fd',
                  borderRadius: '12px',
                  textAlign: 'center',
                }}>
                  <p style={{ fontSize: '32px', fontWeight: 700, color: '#315fa8', margin: '0 0 8px' }}>
                    {avgScore}
                  </p>
                  <p style={{ fontSize: '14px', color: '#667085', margin: 0 }}>
                    Средний балл качества
                  </p>
                </div>
                <div style={{
                  padding: '24px',
                  backgroundColor: '#f5f7fa',
                  borderRadius: '12px',
                  textAlign: 'center',
                }}>
                  <p style={{ fontSize: '32px', fontWeight: 700, color: '#20242c', margin: '0 0 8px' }}>
                    {results.length}
                  </p>
                  <p style={{ fontSize: '14px', color: '#667085', margin: 0 }}>
                    Оценено задач
                  </p>
                </div>
                <div style={{
                  padding: '24px',
                  backgroundColor: '#e6f4ea',
                  borderRadius: '12px',
                  textAlign: 'center',
                }}>
                  <p style={{ fontSize: '32px', fontWeight: 700, color: '#27ae60', margin: '0 0 8px' }}>
                    {results.filter(r => r.quality_score >= 0.8).length}
                  </p>
                  <p style={{ fontSize: '14px', color: '#667085', margin: 0 }}>
                    Высокое качество (&gt;0.8)
                  </p>
                </div>
              </div>
            </div>

            {results.length === 0 ? (
              <div style={{
                backgroundColor: '#ffffff',
                borderRadius: '8px',
                boxShadow: '0 1px 3px rgba(27, 39, 61, 0.08)',
                padding: '48px',
                textAlign: 'center',
                color: '#667085',
              }}>
                <p>Нет данных об оценках качества</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '16px' }}>
                {results.map((result) => (
                  <div
                    key={result.id}
                    onClick={() => setSelectedResult(selectedResult?.id === result.id ? null : result)}
                    style={{
                      backgroundColor: '#ffffff',
                      borderRadius: '8px',
                      boxShadow: '0 1px 3px rgba(27, 39, 61, 0.08)',
                      padding: '16px',
                      cursor: 'pointer',
                      border: selectedResult?.id === result.id ? '2px solid #315fa8' : '1px solid #e9edf3',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <span style={{ fontFamily: 'monospace', fontSize: '13px', color: '#667085' }}>
                        {result.task_id}
                      </span>
                      <span
                        style={{
                          padding: '4px 12px',
                          backgroundColor: `${getScoreColor(result.quality_score)}20`,
                          color: getScoreColor(result.quality_score),
                          borderRadius: '4px',
                          fontSize: '13px',
                          fontWeight: 600,
                        }}
                      >
                        {result.quality_score.toFixed(2)}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#8a94a6', marginBottom: '8px' }}>
                      {new Date(result.timestamp).toLocaleDateString('ru-RU')}
                    </div>
                    {selectedResult?.id === result.id && result.issues.length > 0 && (
                      <div style={{ borderTop: '1px solid #e9edf3', paddingTop: '12px' }}>
                        <p style={{ fontSize: '12px', fontWeight: 600, color: '#20242c', marginBottom: '8px' }}>
                          Проблемы:
                        </p>
                        <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: '#667085' }}>
                          {result.issues.map((issue, i) => (
                            <li key={i}>{issue}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      }
    />
  )
}

export default QualityView
