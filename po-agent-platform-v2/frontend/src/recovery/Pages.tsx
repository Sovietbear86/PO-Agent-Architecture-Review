import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { agent, HarnessQueryResponse } from '../api/client'

type WorkspaceContext = { openAgent(): void }

function useHarness(query: string) {
  const [result, setResult] = useState<HarnessQueryResponse | null>(null)
  useEffect(() => {
    let alive = true
    agent.query({ query }).then(r => alive && setResult(r)).catch(() => alive && setResult(null))
    return () => { alive = false }
  }, [query])
  return result
}

function MetricCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</div>
}

function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  const { openAgent } = useOutletContext<WorkspaceContext>()
  return <div className="page-heading"><div><h1>{title}</h1><p>{subtitle}</p></div><button className="primary-button" onClick={openAgent}>Спросить PO Agent</button></div>
}

function EmptyData({ text }: { text: string }) {
  return <div className="panel empty-panel"><strong>{text}</strong><span>Данные появятся после ответа Harness API.</span></div>
}

export function OverviewPage() {
  const result = useHarness('Дай обзор и риски')
  const data = (result?.data ?? {}) as Record<string, unknown>
  const risks = Array.isArray(data.risks) ? data.risks as Array<Record<string, unknown>> : []
  return <section className="page">
    <PageHeader title="Обзор" subtitle="Состояние продуктов, риски и точки внимания владельца продукта" />
    <div className="metric-grid">
      <MetricCard label="Всего задач" value={String(data.tasks_total ?? '—')} />
      <MetricCard label="В работе" value={String(data.active ?? '—')} />
      <MetricCard label="Завершено" value={String(data.completed ?? '—')} />
      <MetricCard label="Заблокировано" value={String(data.blocked ?? '—')} hint="требуют внимания" />
    </div>
    <div className="content-grid">
      <div className="panel"><div className="panel-title"><strong>Очередь внимания</strong><span>{risks.length}</span></div>
        {risks.length ? risks.map(r => <div className="risk-row" key={String(r.key)}><div><b>{String(r.key)}</b><span>{String(r.title ?? '')}</span></div><em>{String(r.status ?? '')}</em></div>) : <div className="muted">Критичные элементы не обнаружены.</div>}
      </div>
      <div className="panel"><div className="panel-title"><strong>Контур Harness</strong><span className="green-badge">ACTIVE</span></div>
        <div className="fact-row"><span>Runtime</span><b>Harness Core</b></div>
        <div className="fact-row"><span>Adapter</span><b>{String(data.adapter ?? 'fake-as21')}</b></div>
        <div className="fact-row"><span>Evidence</span><b>{result?.evidence.length ?? 0}</b></div>
        <div className="fact-row"><span>Trace</span><b className="mono">{result?.trace_id?.slice(0, 8) ?? '—'}</b></div>
      </div>
    </div>
  </section>
}

export function TasksPage() {
  const result = useHarness('Найди login')
  const data = (result?.data ?? {}) as { tasks?: Array<Record<string, unknown>> }
  const tasks = data.tasks ?? []
  return <section className="page"><PageHeader title="Задачи" subtitle="Поиск, статус, постановка, вложения и task intelligence" />
    <div className="panel toolbar"><input placeholder="Поиск задач" /><button>Фильтры</button><button>+ Локальная задача</button></div>
    <div className="panel"><div className="panel-title"><strong>Задачи</strong><span>{tasks.length}</span></div>
      {tasks.length ? tasks.map(t => <div className="task-row" key={String(t.key)}><div className="task-key">{String(t.key)}</div><div className="task-main"><b>{String(t.title)}</b><span>{String(t.assignee ?? 'Не назначен')}</span></div><div className="status-pill">{String(t.status)}</div></div>) : <EmptyData text="Нет данных по задачам" />}
    </div>
  </section>
}

export function SprintPage() {
  const result = useHarness('Покажи состояние WMB-SPRNT-1')
  const d = (result?.data ?? {}) as Record<string, unknown>
  return <section className="page"><PageHeader title="Спринты" subtitle="Velocity, WIP, throughput, predictability и риски" />
    <div className="metric-grid"><MetricCard label="Scope" value={String(d.total ?? '—')} /><MetricCard label="Completed" value={String(d.completed ?? '—')} /><MetricCard label="Active" value={String(d.active ?? '—')} /><MetricCard label="Готовность" value={`${String(d.completion_percent ?? '—')}%`} /></div>
    <div className="panel"><div className="panel-title"><strong>Текущий спринт</strong><span>{String(d.sprint_id ?? 'WMB-SPRNT-1')}</span></div><div className="muted">Метрики считаются детерминированно. LLM используется только для объяснения.</div></div>
  </section>
}

export function ReleasesPage() {
  const result = useHarness('Риски WMB-2024-Q3')
  const d = (result?.data ?? {}) as Record<string, unknown>
  return <section className="page"><PageHeader title="Релизы" subtitle="Готовность, blockers, dependencies, risk queue и forecast inputs" />
    <div className="metric-grid"><MetricCard label="Scope" value={String(d.total ?? '—')} /><MetricCard label="Completed" value={String(d.completed ?? '—')} /><MetricCard label="Blocked" value={String(d.blocked ?? '—')} /><MetricCard label="Готовность" value={`${String(d.completion_percent ?? '—')}%`} /></div>
    <div className="panel"><div className="panel-title"><strong>{String(d.release_id ?? 'Release')}</strong><span className="green-badge">TRACKED</span></div><div className="muted">Forecast будет активирован только после появления честного исторического baseline.</div></div>
  </section>
}

export function TeamPage() {
  const result = useHarness('Покажи нагрузку команды')
  const d = (result?.data ?? {}) as { workload?: Array<Record<string, unknown>> }
  const rows = d.workload ?? []
  return <section className="page"><PageHeader title="Команда" subtitle="Нагрузка, WIP, blocked, capacity и распределение" />
    <div className="panel"><div className="panel-title"><strong>Активная нагрузка</strong><span>{rows.length}</span></div>
      {rows.length ? rows.map(row => <div className="task-row" key={String(row.member)}><div className="avatar">{String(row.member).slice(0, 1)}</div><div className="task-main"><b>{String(row.member)}</b><span>{String(row.tasks)} задач</span></div><div className="status-pill">{String(row.estimated_hours)} ч</div></div>) : <EmptyData text="Нет данных команды" />}
    </div>
  </section>
}

export function QualityPage() {
  const result = useHarness('Оцени постановку WMB-102')
  return <section className="page"><PageHeader title="Качество" subtitle="Качество постановки задач и evidence-based проверки" />
    <div className="panel"><div className="panel-title"><strong>Task Quality</strong><span className="green-badge">DETERMINISTIC</span></div><pre className="json-box">{result ? JSON.stringify(result.data, null, 2) : 'Загрузка…'}</pre></div>
  </section>
}
