import { useState, useEffect } from 'react'
import { api, tasks as taskApi } from '../api'
import { KanbanBoard, TeamDashboard, SprintMetrics, QualityIndicators, CreateTaskForm } from '../components'

export function POWorkspace() {
  const [activeTab, setActiveTab] = useState('board')
  const [tasks, setTasks] = useState([])

  useEffect(() => {
    const loadTasks = async () => {
      try {
        const response = await taskApi.getAll()
        setTasks(response.data)
      } catch (error) {
        console.error('Failed to load tasks:', error)
      }
    }
    loadTasks()
  }, [])

  const tabs = [
    { id: 'board', label: 'Task Board' },
    { id: 'dashboard', label: 'Team Dashboard' },
    { id: 'metrics', label: 'Sprint Metrics' },
    { id: 'quality', label: 'Quality' },
    { id: 'create', label: 'Create Task' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-4 py-2">
        <h1 className="text-xl font-bold text-gray-800">PO Workspace</h1>
      </nav>

      <div className="max-w-7xl mx-auto p-4">
        {/* Tabs */}
        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="min-h-[600px]">
          {activeTab === 'board' && <KanbanBoard />}
          {activeTab === 'dashboard' && <TeamDashboard />}
          {activeTab === 'metrics' && <SprintMetrics />}
          {activeTab === 'quality' && <QualityIndicators />}
          {activeTab === 'create' && <CreateTaskForm />}
        </div>
      </div>
    </div>
  )
}

export default POWorkspace
