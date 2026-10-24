import { useState, useEffect, useMemo } from 'react'
import { api, team as teamApi, tasks as taskApi } from '../api'
import type { TeamMember } from '../types'

interface Metric {
  label: string
  value: string | number
  trend?: 'up' | 'down' | 'neutral'
  color: string
}

export function TeamDashboard() {
  const [members, setMembers] = useState<TeamMember[]>([])
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  const metrics = useMemo(() => {
    if (members.length === 0) return []

    const totalCapacity = members.reduce((sum, m) => sum + m.capacity_hours, 0)
    const activeTasks = tasks.filter((t: any) => t.status === 'in_progress').length
    const blockedTasks = tasks.filter((t: any) => t.status === 'need_info').length
    const avgSkills = members.reduce((sum, m) => sum + m.skills.length, 0) / members.length

    return [
      { label: 'Team Capacity', value: `${totalCapacity}h`, color: 'blue' },
      { label: 'Active Tasks', value: activeTasks, color: 'purple' },
      { label: 'Blocked Tasks', value: blockedTasks, color: blockedTasks > 0 ? 'red' : 'green' },
      { label: 'Avg Skills', value: avgSkills.toFixed(1), color: 'green' },
    ]
  }, [members, tasks])

  if (loading) return <div className="p-4">Loading dashboard...</div>

  return (
    <div className="space-y-6">
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((metric, i) => (
          <div key={i} className={`bg-${metric.color}-50 rounded-lg p-4 border border-${metric.color}-200`}>
            <p className="text-sm text-gray-600">{metric.label}</p>
            <p className="text-2xl font-bold text-gray-800 mt-1">{metric.value}</p>
          </div>
        ))}
      </div>

      {/* Team Members */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Team Members</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {members.map((member) => (
            <div key={member.login} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
                  <span className="font-bold text-gray-600">
                    {member.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <div>
                  <p className="font-medium">{member.name}</p>
                  <p className="text-xs text-gray-500">{member.role}</p>
                </div>
              </div>
              <div className="space-y-1">
                {member.skills.slice(0, 3).map((skill) => (
                  <span key={skill} className="inline-block px-2 py-1 bg-gray-100 rounded text-xs">
                    {skill}
                  </span>
                ))}
                {member.skills.length > 3 && (
                  <span className="text-xs text-gray-500">+{member.skills.length - 3} more</span>
                )}
              </div>
              <div className="mt-3 text-xs text-gray-500">
                {member.capacity_hours}h/week
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default TeamDashboard
