import { useState, useEffect, useMemo } from 'react'
import { api } from '../api'

export function QualityIndicators() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(true)

  const stats = useMemo(() => {
    if (results.length === 0) return { avg: 0, passing: 0, failing: 0 }

    const avg = results.reduce((sum, r) => sum + r.quality_score, 0) / results.length
    const passing = results.filter((r: any) => r.quality_score >= 0.8).length
    const failing = results.filter((r: any) => r.quality_score < 0.6).length

    return { avg, passing, failing }
  }, [results])

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Average Score</p>
          <p className={`text-2xl font-bold ${stats.avg >= 0.8 ? 'text-green-600' : stats.avg >= 0.6 ? 'text-yellow-600' : 'text-red-600'}`}>
            {stats.avg.toFixed(2)}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Passing (≥0.8)</p>
          <p className="text-2xl font-bold text-green-600">{stats.passing}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <p className="text-sm text-gray-500">Needing Work (&lt;0.6)</p>
          <p className="text-2xl font-bold text-red-600">{stats.failing}</p>
        </div>
      </div>

      {/* Recent Evaluations */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Recent Evaluations</h3>
        <div className="space-y-2">
          {results.slice(0, 5).map((result: any) => (
            <div key={result.id} className="flex justify-between items-center p-2 border-b">
              <div>
                <span className="font-mono text-sm">{result.task_id}</span>
                <span className="ml-2 text-xs text-gray-500">{result.timestamp.split('T')[0]}</span>
              </div>
              <div
                className={`px-2 py-1 rounded text-xs font-medium ${
                  result.quality_score >= 0.8
                    ? 'bg-green-100 text-green-800'
                    : result.quality_score >= 0.6
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                }`}
              >
                {result.quality_score.toFixed(2)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default QualityIndicators
