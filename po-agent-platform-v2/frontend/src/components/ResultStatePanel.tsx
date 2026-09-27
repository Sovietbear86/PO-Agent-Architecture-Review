import type { HarnessQueryResponse } from '../api/client'
import { classifyResult, RESULT_STATE_LABELS, sourceStateMessage } from '../recovery/resultState'

export function ResultStatePanel({ result, compact = false }: { result: HarnessQueryResponse | null | undefined; compact?: boolean }) {
  const state = classifyResult(result)
  if (state === 'SUCCESS_WITH_DATA' || state === 'REAL_EMPTY') return null

  return (
    <div
      data-testid="result-state-panel"
      data-state={state}
      style={{
        padding: compact ? '9px 10px' : '13px 14px',
        border: '1px solid rgba(126,226,255,.16)',
        borderRadius: 10,
        background: 'linear-gradient(145deg, rgba(6,29,49,.82), rgba(4,20,35,.72))',
        color: '#a9c3d2',
        fontSize: 12,
        lineHeight: 1.45,
      }}
    >
      <strong style={{ display: 'block', color: '#e9faff', marginBottom: 3 }}>{RESULT_STATE_LABELS[state]}</strong>
      <span>{sourceStateMessage(state)}</span>
    </div>
  )
}

export default ResultStatePanel
