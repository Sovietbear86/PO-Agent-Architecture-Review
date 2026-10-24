import { useState, useMemo } from 'react'
import { api } from '../api'

interface SprintMetrics {
  velocity: number
  cycleTime: number
  predictability: number
  burndown: number[]
}

export function SprintMetrics() {
  const [metrics, setMetrics] = useState<SprintMetrics>({
    velocity: 0,
    cycleTime: 0,
    predictability: 0,
    burndown: [],
  })

  const computedMetrics = useMemo(() => {
    const completed = metrics.velocity
    const planned = 50 // Mock planned points

    return {
      velocity: completed,
      cycleTime: metrics.cycleTime,
      predictability: (completed / planned) * 100,
      burndown: metrics.burndown,
    }
  }, [metrics])

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Velocity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Velocity</h3>
        <div className="text-4xl font-bold text-blue-600 mb-2">
          {computedMetrics.velocity} pts
        </div>
        <p className="text-sm text-gray-500">Completed points this sprint</p>
      </div>

      {/* Cycle Time */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Cycle Time</h3>
        <div className="text-4xl font-bold text-purple-600 mb-2">
          {computedMetrics.cycleTime} days
        </div>
        <p className="text-sm text-gray-500">Average task completion time</p>
      </div>

      {/* Predictability */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Predictability</h3>
        <div className={`text-4xl font-bold mb-2 ${computedMetrics.predictability >= 80 ? 'text-green-600' : 'text-yellow-600'}`}>
          {computedMetrics.predictability.toFixed(1)}%
        </div>
        <p className="text-sm text-gray-500">Planned vs completed ratio</p>
      </div>
    </div>
  )
}

export default SprintMetrics
