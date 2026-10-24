import { useState, useEffect } from 'react'
import { api } from '../api'

interface PromptEntry {
  id: string
  name: string
  version: number
  content: string
  usage_count: number
  last_used: string
}

export function PromptRegistry() {
  const [prompts, setPrompts] = useState<PromptEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadPrompts = async () => {
      try {
        const response = await api.get('/prompt/registry')
        setPrompts(response.data)
      } catch (error) {
        console.error('Failed to load prompts:', error)
        // Mock data for demo
        setPrompts([
          {
            id: 'prompt-001',
            name: 'Task Summarization',
            version: 3,
            content: 'Summarize the task description...',
            usage_count: 124,
            last_used: '2024-08-05',
          },
          {
            id: 'prompt-002',
            name: 'Sprint Analysis',
            version: 2,
            content: 'Analyze sprint performance based on...',
            usage_count: 87,
            last_used: '2024-08-04',
          },
          {
            id: 'prompt-003',
            name: 'Quality Assessment',
            version: 4,
            content: 'Assess task quality based on...',
            usage_count: 256,
            last_used: '2024-08-05',
          },
        ])
      } finally {
        setLoading(false)
      }
    }
    loadPrompts()
  }, [])

  if (loading) return <div className="p-4">Loading prompts...</div>

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-800 mb-4">Prompt Registry</h2>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-blue-600">{prompts.length}</p>
          <p className="text-sm text-gray-500">Total Prompts</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-purple-600">
            {prompts.reduce((sum, p) => sum + p.usage_count, 0)}
          </p>
          <p className="text-sm text-gray-500">Total Uses</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-2xl font-bold text-green-600">
            {prompts.reduce((sum, p) => sum + p.version, 0)}
          </p>
          <p className="text-sm text-gray-500">Total Versions</p>
        </div>
      </div>

      {/* Prompts List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Version</th>
              <th className="px-4 py-3 text-left">Uses</th>
              <th className="px-4 py-3 text-left">Last Used</th>
            </tr>
          </thead>
          <tbody>
            {prompts.map((prompt) => (
              <tr key={prompt.id} className="border-b hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="font-medium">{prompt.name}</div>
                  <div className="text-xs text-gray-500 truncate max-w-md">{prompt.content}</div>
                </td>
                <td className="px-4 py-3">
                  <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">
                    v{prompt.version}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-600">{prompt.usage_count}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{prompt.last_used}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default PromptRegistry
