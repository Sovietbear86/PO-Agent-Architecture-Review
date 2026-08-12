import { useState } from 'react'
import { AIDashboard, ImprovementCandidates, PromptRegistry, VersionHistory, AgentHistory } from '../components'

export function AI_PDLC_UI() {
  const [activeTab, setActiveTab] = useState('dashboard')

  const tabs = [
    { id: 'dashboard', label: 'AI Dashboard' },
    { id: 'improvements', label: 'Improvements' },
    { id: 'prompts', label: 'Prompts' },
    { id: 'versions', label: 'Versions' },
    { id: 'history', label: 'Agent History' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-4 py-2">
        <h1 className="text-xl font-bold text-gray-800">AI PDLC</h1>
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
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="min-h-[600px]">
          {activeTab === 'dashboard' && <AIDashboard />}
          {activeTab === 'improvements' && <ImprovementCandidates />}
          {activeTab === 'prompts' && <PromptRegistry />}
          {activeTab === 'versions' && <VersionHistory />}
          {activeTab === 'history' && <AgentHistory />}
        </div>
      </div>
    </div>
  )
}

export default AI_PDLC_UI
