import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { agent, HarnessQueryResponse } from '../api/client'
import './OverviewDashboard.css'

type WorkspaceContext = { openAgent(): void }
type QueueRow = { task?: Record<string, unknown>; attention_score?: number; reasons?: string[] }

function useHarness(query: string) {
  const [result, setResult] = useState<HarnessQueryResponse | null>(null)
  useEffect(() => {
    let alive = true
    agent.query({ query }).then(r => alive && setResult(r)).catch(() => alive && setResult(null))
    return () => { alive = false }
  }, [query])
  return result
}

function Meta({ result }: { result: HarnessQueryResponse | null }) {
  return <div className="filter-status"><span>Skill: {result?.skill?.id ?? '—'}</span><span>Evidence: {result?.evidence.length ?? 0}</span><span>Trace: {result?.trace_id?.slice(0,8) ?? '—'}</span></div>
}

function Metric({ label, value, hint }: { label: string; value: unknown; hint?: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{String(value ?? '—')}</strong>{hint && <small>{hint}</small>}</div>
}

export function OverviewDashboard() {
  const { openAgent } = useOutletContext<WorkspaceContext>()
  const overview = useHarness('Дай обзор и риски')
  const attention = useHarness('Покажи очередь внимания')
  const brief = useHarness('Сделай daily brief')
  const status = useHarness('Сделай status report')
  const od = (overview?.data ?? {}) as Record<string, unknown>
  const ad = (attention?.data ?? {}) as { count?: number; queue?: QueueRow[]; scoring_version?: string }
  const bd = (brief?.data ?? {}) as Record<string, unknown>
  const sd = (status?.data ?? {}) as { completion_percent?: number; by_product?: Record<string, { total?: number; completed?: number; blocked?: number }> }
  const queue = ad.queue ?? []
  const products = Object.entries(sd.by_product ?? {})

  return <section className="page">
    <div className="page-heading"><div><h1>Обзор</h1><p>Единая точка внимания PO: портфель, риски, brief и статус продуктов</p></div><button className="primary-button" onClick={openAgent}>Спросить PO Agent</button></div>
    <div className="metric-grid">
      <Metric label="Всего задач" value={od.tasks_total} />
      <Metric label="В работе" value={od.active} />
      <Metric label="Заблокировано" value={od.blocked} hint="требуют внимания" />
      <Metric label="Готовность портфеля" value={`${String(sd.completion_percent ?? '—')}%`} />
    </div>

    <div className="content-grid">
      <div className="panel"><div className="panel-title"><strong>Очередь внимания PO</strong><span>{ad.count ?? queue.length}</span></div>
        {queue.length ? queue.map((row, index) => { const task = row.task ?? {}; return <div className="attention-row" key={String(task.key ?? index)}><div><b>{String(task.key ?? '')}</b><strong>{String(task.title ?? '')}</strong><span>{(row.reasons ?? []).join(' · ')}</span></div><em>{String(row.attention_score ?? '')}</em></div> }) : <div className="muted">Нет элементов, требующих вмешательства PO.</div>}
        <div className="queue-version">Scoring: {ad.scoring_version ?? '—'}</div><Meta result={attention} />
      </div>
      <div className="panel"><div className="panel-title"><strong>Daily Brief</strong><span className="green-badge">GROUNDED</span></div><p className="brief-copy">{brief?.answer ?? 'Загрузка…'}</p>
        <div className="fact-row"><span>Активно</span><b>{String(bd.active ?? '—')}</b></div><div className="fact-row"><span>Blocked</span><b>{String(bd.blocked ?? '—')}</b></div><div className="fact-row"><span>Без исполнителя</span><b>{String(bd.unassigned ?? '—')}</b></div>
        {brief?.warnings.length ? <div className="warning">{brief.warnings.join(' · ')}</div> : null}<Meta result={brief} />
      </div>
    </div>

    <div className="panel product-status-panel"><div className="panel-title"><strong>Статус продуктов</strong><span>{products.length}</span></div>
      {products.length ? <div className="product-status-grid">{products.map(([name, row]) => <div className="product-status-card" key={name}><strong>{name}</strong><div><span>Всего</span><b>{row.total ?? 0}</b></div><div><span>Завершено</span><b>{row.completed ?? 0}</b></div><div><span>Blocked</span><b>{row.blocked ?? 0}</b></div></div>)}</div> : <div className="muted">Нет продуктовых данных.</div>}
      <Meta result={status} />
    </div>
  </section>
}
