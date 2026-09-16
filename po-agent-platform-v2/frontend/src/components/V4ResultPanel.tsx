import { HarnessQueryResponse } from '../api/client'

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

  const key = record.key ?? record.id ?? record.sprint_id ?? record.source_id
  const title = record.title ?? record.name ?? record.summary ?? record.status
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

function stateFor(result: HarnessQueryResponse): string {
  if (result.status === 'FAILED') {
    return result.warnings.includes('source_unavailable') || result.warnings.includes('source_capability_unavailable')
      ? 'SOURCE_UNAVAILABLE'
      : 'ERROR'
  }
  if (result.status === 'PARTIAL') return 'PARTIAL_DATA'
  if (result.status === 'NEEDS_CLARIFICATION') return 'NEEDS_CLARIFICATION'
  const count = findField(result.data, 'count')
  if (count === 0) return 'REAL_EMPTY'
  return 'SUCCESS_WITH_DATA'
}

function structuredRows(data: unknown): unknown[] {
  const candidates = ['tasks', 'sprints', 'results', 'matches', 'timeline', 'durations', 'risks', 'dependencies']
  for (const field of candidates) {
    const value = findField(data, field)
    if (Array.isArray(value)) return value
  }
  const task = findField(data, 'task')
  return task ? [task] : []
}

export function V4ResultPanel({ result }: Props) {
  if (result.runtime !== 'agent_core_v4') return null

  const state = stateFor(result)
  const widget = result.ui?.preferred_widget
  const rows = structuredRows(result.data)

  return (
    <div data-testid="v4-result-panel" style={{ marginTop: 10, border: '1px solid #e3e8ef', borderRadius: 10, background: '#fff', overflow: 'hidden' }}>
      <div style={{ padding: '9px 11px', display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', borderBottom: '1px solid #eef1f5', fontSize: 11, color: '#667085' }}>
        <strong style={{ color: '#344054' }}>V4</strong>
        <span>{state}</span>
        {widget && <span>widget: {widget}</span>}
        {result.ui?.result_kind && <span>kind: {result.ui.result_kind}</span>}
      </div>

      {rows.length > 0 && (
        <div data-testid="v4-structured-result" style={{ maxHeight: 260, overflow: 'auto' }}>
          {rows.slice(0, 50).map((row, index) => (
            <div key={`${rowLabel(row)}-${index}`} style={{ padding: '8px 11px', borderBottom: '1px solid #f2f4f7', fontSize: 12, color: '#344054' }}>
              {rowLabel(row)}
            </div>
          ))}
          {rows.length > 50 && <div style={{ padding: '8px 11px', fontSize: 11, color: '#667085' }}>Показаны первые 50 из {rows.length}</div>}
        </div>
      )}

      {result.evidence.length > 0 && (
        <details style={{ padding: '8px 11px', fontSize: 11, color: '#667085' }}>
          <summary style={{ cursor: 'pointer' }}>Evidence: {result.evidence.length}</summary>
          <div style={{ marginTop: 7, display: 'grid', gap: 5 }}>
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
