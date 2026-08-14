import { useState, useEffect } from 'react'
import { api } from '../api'

interface VersionEntry {
  id: string
  config_type: string
  version: number
  changed_by: string
  timestamp: string
  changes: string[]
  status: 'active' | 'deprecated' | 'archived'
}

export function VersionHistory() {
  const [versions, setVersions] = useState<VersionEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadVersions = async () => {
      try {
        const response = await api.get('/version/history')
        setVersions(response.data)
      } catch (error) {
        console.error('Failed to load versions:', error)
        // Mock data for demo
        setVersions([
          {
            id: 'ver-001',
            config_type: 'Team Config',
            version: 5,
            changed_by: 'Kalachanov.V.V',
            timestamp: '2024-08-01 10:30',
            changes: ['Updated capacity hours', 'Added new member'],
            status: 'active',
          },
          {
            id: 'ver-002',
            config_type: 'Quality Rules',
            version: 3,
            changed_by: 'Garanin.R.V',
            timestamp: '2024-07-28 14:15',
            changes: ['Threshold adjusted to 0.8'],
            status: 'active',
          },
          {
            id: 'ver-003',
            config_type: 'Prompt Template',
            version: 2,
            changed_by: 'Agataeva.A.Z',
            timestamp: '2024-07-25 09:00',
            changes: ['Updated summary prompt'],
            status: 'deprecated',
          },
        ])
      } finally {
        setLoading(false)
      }
    }
    loadVersions()
  }, [])

  if (loading) return <div className="p-4">Loading versions...</div>

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">Version History</h2>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-blue-600">
            {versions.filter((v) => v.status === 'active').length}
          </p>
          <p className="text-sm text-gray-500">Active Configs</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-purple-600">
            {versions.reduce((sum, v) => sum + v.version, 0)}
          </p>
          <p className="text-sm text-gray-500">Total Versions</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-green-600">
            {new Set(versions.map((v) => v.config_type)).size}
          </p>
          <p className="text-sm text-gray-500">Config Types</p>
        </div>
      </div>

      {/* Versions List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left">Type</th>
              <th className="px-4 py-3 text-left">Version</th>
              <th className="px-4 py-3 text-left">Changed By</th>
              <th className="px-4 py-3 text-left">Timestamp</th>
              <th className="px-4 py-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((version) => (
              <tr key={version.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3">{version.config_type}</td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                    v{version.version}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm">{version.changed_by}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{version.timestamp}</td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      version.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : version.status === 'deprecated'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {version.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default VersionHistory
