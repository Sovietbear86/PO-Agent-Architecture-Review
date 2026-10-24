import { useState, useEffect } from 'react'
import { api } from '../api'

interface Trace {
  id: string
  query: string
  response: string
  confidence: number
  memory_used: boolean
  memory_count: number
  timestamp: string
  status: 'success' | 'error'
}

export function AgentHistory() {
  const [traces, setTraces] = useState<Trace[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadTraces = async () => {
      try {
        const response = await api.get('/agent/history')
        setTraces(response.data)
      } catch (error) {
        console.error('Failed to load traces:', error)
        // Mock data for demo
        setTraces([
          {
            id: 'trace-001',
            query: 'Show tasks from sprint WMB-SPRNT-4',
            response: 'Found 12 tasks in the sprint',
            confidence: 0.95,
            memory_used: false,
            memory_count: 0,
            timestamp: '2024-08-05 10:30:00',
            status: 'success',
          },
          {
            id: 'trace-002',
            query: 'Analyze sprint health',
            response: 'Sprint health score: 0.78',
            confidence: 0.88,
            memory_used: true,
            memory_count: 142,
            timestamp: '2024-08-05 09:15:00',
            status: 'success',
          },
          {
            id: 'trace-003',
            query: 'What is velocity?',
            response: 'Team velocity is 24 points',
            confidence: 0.92,
            memory_used: true,
            memory_count: 142,
            timestamp: '2024-08-04 14:20:00',
            status: 'success',
          },
        ])
      } finally {
        setLoading(false)
      }
    }
    loadTraces()
  }, [])

  if (loading) return <div className="p-4">Loading traces...</div>

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">Agent History / Traces</h2>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-gray-600">{traces.length}</p>
          <p className="text-sm text-gray-500">Total Traces</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-green-600">
            {traces.filter((t) => t.status === 'success').length}
          </p>
          <p className="text-sm text-gray-500">Success</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-blue-600">
            {traces.filter((t) => t.memory_used).length}
          </p>
          <p className="text-sm text-gray-500">Memory Used</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-purple-600">
            {(traces.reduce((sum, t) => sum + t.memory_count, 0) / traces.length).toFixed(0)}
          </p>
          <p className="text-sm text-gray-500">Avg Memory</p>
        </div>
      </div>

      {/* Traces List */}
      <div className="space-y-3">
        {traces.slice(0, 10).map((trace) => (
          <div key={trace.id} className="bg-white rounded-lg shadow p-4">
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-3">
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${
                    trace.status === 'success'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {trace.status}
                </span>
                <span className="text-xs text-gray-500">{trace.timestamp}</span>
              </div>
              <span className="text-xs text-gray-500">trace-{trace.id.slice(-4)}</span>
            </div>
            <div className="mb-3">
              <p className="text-sm text-gray-500 mb-1">Query:</p>
              <p className="text-sm font-medium text-gray-800">{trace.query}</p>
            </div>
            <div className="mb-3">
              <p className="text-sm text-gray-500 mb-1">Response:</p>
              <p className="text-sm text-gray-700">{trace.response}</p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <span>
                Confidence: <span className={`font-medium ${trace.confidence >= 0.8 ? 'text-green-600' : 'text-yellow-600'}`}>{trace.confidence.toFixed(2)}</span>
              </span>
              <span>
                Memory: <span className="font-medium">{trace.memory_used ? trace.memory_count : 'none'}</span>
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AgentHistory
