import { useState, useEffect } from 'react'
import { api } from '../api'

interface QualityMetric {
  name: string
  value: number
  target: number
  status: 'pass' | 'warn' | 'fail'
}

export function AIDashboard() {
  const [metrics, setMetrics] = useState<QualityMetric[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const response = await api.get('/metrics/quality')
        setMetrics(response.data)
      } catch (error) {
        console.error('Failed to load metrics:', error)
        // Mock data for demo
        setMetrics([
          { name: 'Task Summarization', value: 0.85, target: 0.8, status: 'pass' },
          { name: 'Sprint Health Analysis', value: 0.78, target: 0.8, status: 'warn' },
          { name: 'Team Performance', value: 0.92, target: 0.9, status: 'pass' },
          { name: 'Release Readiness', value: 0.65, target: 0.8, status: 'fail' },
        ])
      } finally {
        setLoading(false)
      }
    }
    loadMetrics()
  }, [])

  if (loading) return <div className="p-4">Loading dashboard...</div>

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">AI PDLC Dashboard</h2>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, i) => (
          <div
            key={i}
            className={`p-4 rounded-lg border-2 ${
              metric.status === 'pass'
                ? 'bg-green-50 border-green-300'
                : metric.status === 'warn'
                  ? 'bg-yellow-50 border-yellow-300'
                  : 'bg-red-50 border-red-300'
            }`}
          >
            <p className="text-sm text-gray-600">{metric.name}</p>
            <div className="mt-2">
              <span
                className={`text-3xl font-bold ${
                  metric.status === 'pass'
                    ? 'text-green-600'
                    : metric.status === 'warn'
                      ? 'text-yellow-600'
                      : 'text-red-600'
                }`}
              >
                {metric.value.toFixed(2)}
              </span>
              <span className="text-sm text-gray-500 ml-2">/ {metric.target}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Quality Overview</h3>
          <div className="space-y-3">
            {metrics.map((metric) => (
              <div key={metric.name} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{metric.name}</span>
                <span
                  className={`text-xs px-2 py-1 rounded-full ${
                    metric.status === 'pass'
                      ? 'bg-green-100 text-green-800'
                      : metric.status === 'warn'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                  }`}
                >
                  {metric.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">AI Status</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">AI Agent Active</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Memory: 142 entries</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Prompts: 23 versions</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AIDashboard
