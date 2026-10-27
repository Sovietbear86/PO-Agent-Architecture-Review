import { HarnessQueryResponse } from '../api/client'
import { classifyResult, RESULT_STATE_LABELS, sourceStateMessage } from '../recovery/resultState'

type Props = {
  result: HarnessQueryResponse
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : undefined
}

// The V4 'results' array contains internal planner envelopes, not user rows.
// Show only explicit business collections from the execution payload.
const BUSINESS_COLLECTIONS = ['tasks', 'sprints', 'matches', 'candidates', 'queue', 'timeline', 'durations', 'risks', 'risk_queue', 'dependencies', 'members', 'worklogs', 'entries'] as const
const BUSINESS_LABEL_FIELDS = ['key', 'id', 'sprint_id', 'task_code', 'source_id', 'member', 'full_name', 'title', 'name', 'summary', 'status', 'date', 'duration_hours'] as const

function safeText(value: unknown): string | undefined {
  if (typeof value === 'string' && value.trim()) return value
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  return undefined
}

function rowLabel(row: unknown): string | undefined {
  if (typeof row === 'string' || typeof row === 'number') return safeText(row)
  const record = asRecord(row)
  if (!record) return undefined
  const task = asRecord(record.task)
  const base = task ?? record
  const bits = BUSINESS_LABEL_FIELDS.map(field => safeText(base[field])).filter((x): x is string => Boolean(x))
  if (bits.length) return [...new Set(bits)].slice(0, 3).join(' · ')
  if (safeText(record.from) || safeText(record.to)) {
    return [safeText(record.from), '→', safeText(record.to)].filter(Boolean).join(' ')
  }
  // Do NOT stringify unknown objects: they may be planner steps containing
  // capability_id, arguments, arbitrary AS21 payloads and internal traces.
  return undefined
}

function structuredRows(data: unknown): string[] {
  const root = asRecord(data)
  if (!root) return []
  const candidates: Record<string, unknown>[] = [root]
  const executionResults = Array.isArray(root.results) ? root.results : []
  for (const result of executionResults) {
    const envelope = asRecord(result)
    const businessData = asRecord(envelope?.data)
    if (businessData) candidates.push(businessData)
  }
  for (const record of candidates) {
    for (const field of BUSINESS_COLLECTIONS) {
      const value = record[field]
      if (!Array.isArray(value)) continue
      return value.map(rowLabel).filter((x): x is string => Boolean(x))
    }
    const task = record.task
    const singleTask = task ? rowLabel(task) : undefined
    if (singleTask) return [singleTask]
  }
  return []
}

export function V4ResultPanel({ result }: Props) {
  if (result.runtime !== 'agent_core_v4') return null

  const state = classifyResult(result)
  const rows = structuredRows(result.data)

  return (
    <div data-testid="v4-result-panel" className="v4-result-panel">
      <div className="v4-result-header">
        <strong>V4</strong>
        <span className={'v4-state v4-state-' + state.toLowerCase()}>{RESULT_STATE_LABELS[state]}</span>

      </div>

      {state !== 'SUCCESS_WITH_DATA' && state !== 'REAL_EMPTY' && (
        <div className="v4-state-message">{sourceStateMessage(state)}</div>
      )}

      {state === 'REAL_EMPTY' && rows.length === 0 && (
        <div className="v4-state-message">{sourceStateMessage(state)}</div>
      )}

      {rows.length > 0 && (
        <div data-testid="v4-structured-result" className="v4-structured-result">
          {rows.slice(0, 50).map((row, index) => (
            <div key={`${row}-${index}`} className="v4-structured-row">
              {row}
            </div>
          ))}
          {rows.length > 50 && <div className="v4-structured-more">Показаны первые 50 из {rows.length}</div>}
        </div>
      )}

      {result.evidence.length > 0 && (
        <details className="v4-evidence-details">
          <summary>Источники: {result.evidence.length}</summary>
          <div className="v4-evidence-list">
            {result.evidence.slice(0, 20).map((item, index) => (
              <div key={`${item.source}-${item.entity_id || index}`}>{item.source} · {item.entity_id || item.label} · {item.label}</div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}

export default V4ResultPanel
