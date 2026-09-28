import { HarnessQueryResponse } from '../api/client'
import { classifyResult, RESULT_STATE_LABELS, sourceStateMessage } from '../recovery/resultState'

type Props = {
  result: HarnessQueryResponse
}

function asRecord(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : undefined
}

function findField(value: unknown, key: string): unknown {
  const record = asRecord(value)
  if (!record) return undefined
  if (key in record) return record[key]
  for (const child of Object.values(record)) {
    const nested = findField(child, key)
    if (nested !== undefined) return nested
  }
  return undefined
}

function rowLabel(row: unknown): string {
  const record = asRecord(row)
  if (!record) return String(row ?? '')

  // Attachment-search rows wrap the canonical task beside attachment metadata.
  const nestedTask = asRecord(record.task)
  if (nestedTask) {
    const key = nestedTask.key ?? nestedTask.id
    const title = nestedTask.title ?? nestedTask.summary
    const attachments = Array.isArray(record.attachments) ? `attachments: ${record.attachments.length}` : undefined
    return [key, title, attachments].filter(Boolean).map(String).join(' · ') || JSON.stringify(record)
  }

  const key = record.key ?? record.id ?? record.sprint_id ?? record.source_id ?? record.member ?? record.full_name
  const title = record.title ?? record.name ?? record.summary ?? record.status ?? record.professional_profile
  if (key || title) return [key, title].filter(Boolean).map(String).join(' · ')

  // Timeline rows remain compact and readable without teaching the UI business
  // semantics; the UIContract still decides only presentation metadata.
  if (record.from !== undefined || record.to !== undefined) {
    return [record.from, '→', record.to, record.status, record.hours !== undefined ? `${record.hours} h` : undefined]
      .filter(value => value !== undefined && value !== null && value !== '')
      .map(String)
      .join(' ')
  }
  return JSON.stringify(record)
}

function structuredRows(data: unknown): unknown[] {
  const candidates = ['tasks', 'sprints', 'results', 'matches', 'candidates', 'queue', 'timeline', 'durations', 'risks', 'risk_queue', 'dependencies', 'members']
  for (const field of candidates) {
    const value = findField(data, field)
    if (Array.isArray(value)) return value
  }
  const task = findField(data, 'task')
  return task ? [task] : []
}

export function V4ResultPanel({ result }: Props) {
  if (result.runtime !== 'agent_core_v4') return null

  const state = classifyResult(result)
  const widget = result.ui?.preferred_widget
  const rows = structuredRows(result.data)

  return (
    <div data-testid="v4-result-panel" className="v4-result-panel">
      <div className="v4-result-header">
        <strong>V4</strong>
        <span className={'v4-state v4-state-' + state.toLowerCase()}>{RESULT_STATE_LABELS[state]}</span>
        {widget && <span>widget: {widget}</span>}
        {result.ui?.result_kind && <span>kind: {result.ui.result_kind}</span>}
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
            <div key={`${rowLabel(row)}-${index}`} className="v4-structured-row">
              {rowLabel(row)}
            </div>
          ))}
          {rows.length > 50 && <div className="v4-structured-more">Показаны первые 50 из {rows.length}</div>}
        </div>
      )}

      {result.evidence.length > 0 && (
        <details className="v4-evidence-details">
          <summary>Evidence: {result.evidence.length}</summary>
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
