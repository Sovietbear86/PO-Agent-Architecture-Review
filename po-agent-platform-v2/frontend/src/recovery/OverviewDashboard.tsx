import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { HarnessQueryResponse } from '../api/client'
import { ResultStatePanel } from '../components/ResultStatePanel'
import { RichAnswer } from '../components/agent/RichAnswer'
import { classifyResult, getCapabilityData, stateAllowsBusinessData } from './resultState'
import './OverviewDashboard.css'
import { SnapshotRefresh, useSnapshotHarness } from './pageSnapshot'

type WorkspaceContext = { openAgent(): void }
type QueueRow = { task?: Record<string, unknown>; attention_score?: number; reasons?: string[] }

function Meta({ result }: { result: HarnessQueryResponse | null }) {
  return <div className="filter-status"><span>Skill: {result?.skill?.id ?? '—'}</span><span>Evidence: {result?.evidence.length ?? 0}</span><span>Trace: {result?.trace_id?.slice(0,8) ?? '—'}</span></div>
}

function Metric({ label, value, hint }: { label: string; value: unknown; hint?: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{String(value ?? '—')}</strong>{hint && <small>{hint}</small>}</div>
}

export function OverviewDashboard() {
  const { openAgent } = useOutletContext<WorkspaceContext>()
  const [refreshNonce, setRefreshNonce] = useState(0)
  const attentionQ = useSnapshotHarness('overview', 'Покажи очередь внимания', refreshNonce)
  const briefQ = useSnapshotHarness('overview', 'Сделай daily brief', refreshNonce)
  const statusQ = useSnapshotHarness('overview', 'Сделай status report', refreshNonce)
  const attention = attentionQ.result
  const brief = briefQ.result
  const status = statusQ.result
  const ad = getCapabilityData(attention) as { count?: number; queue?: QueueRow[]; scoring_version?: string }
  const bd = getCapabilityData(brief) as {
    active?: number
    blocked?: number
    unassigned?: number
    completed?: number
    attention_count?: number
    top_attention?: QueueRow[]
    spaces?: Array<{ space?: string; sprint_id?: string; state?: string; task_count?: number | null }>
  }
  const sd = getCapabilityData(status) as {
    active?: number
    completed?: number
    blocked?: number
    completion_percent?: number
    by_product?: Record<string, { total?: number; completed?: number; blocked?: number }>
    by_space_tasks?: Record<string, { state?: string; total?: number | null; active?: number | null; completed?: number | null; blocked?: number | null; breakdown_state?: string }>
  }
  const queue = ad.queue ?? []
  const spaces = Object.entries(sd.by_space_tasks ?? {})
  const attentionState = classifyResult(attention)
  const briefState = classifyResult(brief)
  const statusState = classifyResult(status)

  return <section className="page page-overview">
    <div className="page-heading"><div><h1>Обзор</h1><p>Единая точка внимания PO: портфель, риски, brief и задачи по пространствам</p></div><div className="page-heading-actions"><SnapshotRefresh updatedAt={[attentionQ.updatedAt, briefQ.updatedAt, statusQ.updatedAt]} refreshing={attentionQ.refreshing || briefQ.refreshing || statusQ.refreshing} refreshError={attentionQ.refreshError || briefQ.refreshError || statusQ.refreshError} onRefresh={() => setRefreshNonce(value => value + 1)} /><button className="primary-button" onClick={openAgent}>Спросить PO Agent</button></div></div>
    <div className="metric-grid">
      <Metric label="Активно" value={stateAllowsBusinessData(statusState) ? (sd.active ?? '—') : '—'} />
      <Metric label="Завершено" value={stateAllowsBusinessData(statusState) ? (sd.completed ?? '—') : '—'} />
      <Metric label="Заблокировано" value={stateAllowsBusinessData(statusState) ? (sd.blocked ?? '—') : '—'} hint="требуют внимания" />
      <Metric label="Готовность портфеля" value={stateAllowsBusinessData(statusState) ? `${String(sd.completion_percent ?? '—')}%` : '—'} />
    </div>

    <div className="content-grid">
      <div className="panel overview-twin-panel"><div className="panel-title"><strong>Очередь внимания PO</strong><span>{ad.count ?? queue.length}</span></div>
        <div className="overview-scroll-body">
          {stateAllowsBusinessData(attentionState)
            ? (queue.length
              ? queue.map((row, index) => { const task = row.task ?? {}; return <div className="attention-row" key={String(task.key ?? index)}><div><b>{String(task.key ?? '')}</b><strong>{String(task.title ?? '')}</strong><span>{(row.reasons ?? []).join(' · ')}</span></div><em>{String(row.attention_score ?? '')}</em></div> })
              : <div className="muted">Источник подтвердил: элементов, требующих вмешательства PO, нет.</div>)
            : <ResultStatePanel result={attention} compact />}
        </div>
        {stateAllowsBusinessData(attentionState) && queue.length > 10 && <div className="queue-version">Всего {queue.length} задач · прокрутите список</div>}
        {stateAllowsBusinessData(attentionState) && <div className="queue-version">Scoring: {ad.scoring_version ?? '—'}</div>}<Meta result={attention} />
      </div>
      <div className="panel overview-twin-panel"><div className="panel-title"><strong>Daily Brief</strong><span className="green-badge">GROUNDED</span></div>
        <div className="overview-scroll-body">
        {stateAllowsBusinessData(briefState)
          ? <div className="brief-copy"><RichAnswer text={brief?.answer ?? ''} /></div>
          : <ResultStatePanel result={brief} compact />}
        {stateAllowsBusinessData(briefState) && <>
          <div className="fact-row"><span>Активно</span><b>{String(bd.active ?? '—')}</b></div>
          <div className="fact-row"><span>Завершено</span><b>{String(bd.completed ?? '—')}</b></div>
          <div className="fact-row"><span>Blocked</span><b>{String(bd.blocked ?? '—')}</b></div>
          <div className="fact-row"><span>Без исполнителя</span><b>{String(bd.unassigned ?? '—')}</b></div>
          <div className="fact-row"><span>Точек внимания</span><b>{String(bd.attention_count ?? '—')}</b></div>
          {(bd.top_attention?.length ?? 0) > 0 && <div className="brief-section"><strong>Top attention</strong>{bd.top_attention!.map((row, index) => { const task = row.task ?? {}; return <div className="brief-attention-row" key={String(task.key ?? index)}><span><b>{String(task.key ?? '')}</b> {String(task.title ?? '')}</span><em>{String(row.attention_score ?? '')}</em></div> })}</div>}
          {(bd.spaces?.length ?? 0) > 0 && <div className="brief-section"><strong>Текущие спринты</strong>{bd.spaces!.map((row, index) => <div className="fact-row compact" key={String(row.space ?? index)}><span>{String(row.space ?? '—')} · {String(row.sprint_id ?? row.state ?? '—')}</span><b>{row.task_count ?? '—'}</b></div>)}</div>}
        </>}
        </div>
        {brief?.warnings.length ? <div className="warning">{brief.warnings.join(' · ')}</div> : null}<Meta result={brief} />
      </div>
    </div>

    <div className="panel product-status-panel"><div className="panel-title"><strong>Задачи по пространствам</strong><span>{spaces.length}</span></div><div className="form-note">Только задачи, назначенные участникам команды из team_members.yaml; одинаковые задачи дедуплицируются по ключу.</div>
      {stateAllowsBusinessData(statusState)
        ? (spaces.length
          ? <div className="product-status-grid">{spaces.map(([name, row]) => <div className="product-status-card" key={name}>
              <strong>{name}</strong>
              {row.state === 'SOURCE_BACKED' ? <>
                <div><span>Всего задач</span><b>{row.total ?? '—'}</b></div>
                <div><span>Активно</span><b>{row.active ?? '—'}</b></div>
                <div><span>Завершено</span><b>{row.completed ?? '—'}</b></div>
                <div><span>Blocked</span><b>{row.blocked ?? '—'}</b></div>
              </> : <div className="space-source-note">Часть данных участников команды недоступна · без ложных итогов</div>}
            </div>)}</div>
          : <div className="muted">Источник подтвердил отсутствие данных по пространствам.</div>)
        : <ResultStatePanel result={status} compact />}
      <Meta result={status} />
    </div>
  </section>
}
