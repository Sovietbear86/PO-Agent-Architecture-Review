import { useState, useEffect } from 'react'
import { api } from '../api'

interface ImprovementCandidate {
  id: string
  title: string
  category: string
  confidence: number
  evidence: string[]
  status: 'new' | 'reviewed' | 'implemented' | 'rejected'
  created_at: string
}

export function ImprovementCandidates() {
  const [candidates, setCandidates] = useState<ImprovementCandidate[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadCandidates = async () => {
      try {
        const response = await api.get('/improvement/candidates')
        setCandidates(response.data)
      } catch (error) {
        console.error('Failed to load candidates:', error)
        // Mock data for demo
        setCandidates([
          {
            id: 'IC-001',
            title: 'Add sprint velocity tracking',
            category: 'metrics',
            confidence: 0.85,
            evidence: ['Sprint 4 data available', 'Velocity consistent'],
            status: 'new',
            created_at: '2024-08-01',
          },
          {
            id: 'IC-002',
            title: 'Improve task assignment algorithm',
            category: 'workflow',
            confidence: 0.72,
            evidence: ['Team capacity data', 'Skill matching'],
            status: 'reviewed',
            created_at: '2024-08-02',
          },
        ])
      } finally {
        setLoading(false)
      }
    }
    loadCandidates()
  }, [])

  if (loading) return <div className="p-4">Loading candidates...</div>

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">Improvement Candidates</h2>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        {['new', 'reviewed', 'implemented', 'rejected'].map((status) => (
          <div key={status} className="bg-white rounded-lg shadow p-4 text-center">
            <p className="text-2xl font-bold text-gray-700">
              {candidates.filter((c) => c.status === status).length}
            </p>
            <p className="text-sm text-gray-500 uppercase">{status}</p>
          </div>
        ))}
      </div>

      {/* Candidates List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left">ID</th>
              <th className="px-4 py-3 text-left">Title</th>
              <th className="px-4 py-3 text-left">Category</th>
              <th className="px-4 py-3 text-left">Confidence</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Date</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((candidate) => (
              <tr key={candidate.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-sm">{candidate.id}</td>
                <td className="px-4 py-3">{candidate.title}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {candidate.category}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-full bg-gray-200 rounded-full h-2 w-24">
                      <div
                        className={`h-2 rounded-full ${
                          candidate.confidence >= 0.8
                            ? 'bg-green-500'
                            : candidate.confidence >= 0.6
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                        }`}
                        style={{ width: `${candidate.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-sm">{candidate.confidence.toFixed(2)}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      candidate.status === 'new'
                        ? 'bg-gray-100 text-gray-800'
                        : candidate.status === 'reviewed'
                          ? 'bg-blue-100 text-blue-800'
                          : candidate.status === 'implemented'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {candidate.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">{candidate.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default ImprovementCandidates
