import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { agent, HarnessQueryResponse } from '../api/client'

type WorkspaceContext = { openAgent(): void }
type TaskRow = Record<string, unknown>
type LocalTask = { id: string; title: string; description: string; owner: string; createdAt: string }

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

function TaskCard({ task, onOpen }: { task: TaskRow; onOpen(task: TaskRow): void }) {
  return <button className="task-card" onClick={() => onOpen(task)}>
    <div className="task-card-top"><span className="task-key">{String(task.key ?? '')}</span><span className="status-pill">{String(task.status ?? '')}</span></div>
    <strong>{String(task.title ?? '')}</strong>
    <div className="task-card-meta"><span>{String(task.assignee ?? 'Не назначен')}</span><span>{String(task.priority ?? '—')}</span></div>
  </button>
}

function LocalTaskDrawer({ open, onClose, onCreate }: { open: boolean; onClose(): void; onCreate(task: LocalTask): void }) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [owner, setOwner] = useState('')
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!title.trim()) return
    onCreate({ id: `LOCAL-${Date.now()}`, title: title.trim(), description: description.trim(), owner: owner.trim(), createdAt: new Date().toISOString() })
    setTitle(''); setDescription(''); setOwner(''); onClose()
  }
  return <>
    <div className={`drawer-scrim ${open ? 'visible' : ''}`} onClick={onClose} />
    <aside className={`task-drawer ${open ? 'task-drawer-open' : ''}`} aria-hidden={!open}>
      <div className="agent-header"><div><div className="agent-kicker">LOCAL TASK</div><strong>Создать локальную задачу</strong></div><button className="icon-button" onClick={onClose}>×</button></div>
      <form className="task-form" onSubmit={submit}>
        <label>Название<input value={title} onChange={e => setTitle(e.target.value)} placeholder="Что нужно сделать" autoFocus={open} /></label>
        <label>Описание<textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Контекст, ожидаемый результат, ограничения" rows={7} /></label>
        <label>Ответственный<input value={owner} onChange={e => setOwner(e.target.value)} placeholder="Опционально" /></label>
        <div className="form-note">Локальная задача сохраняется только в браузере и не пишет в AS21 без отдельного approval/write capability.</div>
        <div className="form-actions"><button type="button" onClick={onClose}>Отмена</button><button className="primary-button" type="submit" disabled={!title.trim()}>Создать</button></div>
      </form>
    </aside>
  </>
}

function TaskDetailsDrawer({ task, onClose }: { task: TaskRow | null; onClose(): void }) {
  return <>
    <div className={`drawer-scrim ${task ? 'visible' : ''}`} onClick={onClose} />
    <aside className={`task-drawer ${task ? 'task-drawer-open' : ''}`} aria-hidden={!task}>
      <div className="agent-header"><div><div className="agent-kicker">TASK DETAILS</div><strong>{String(task?.key ?? '')}</strong></div><button className="icon-button" onClick={onClose}>×</button></div>
      {task && <div className="task-details">
        <h2>{String(task.title ?? '')}</h2>
        <div className="details-grid"><span>Статус</span><b>{String(task.status ?? '—')}</b><span>Исполнитель</span><b>{String(task.assignee ?? 'Не назначен')}</b><span>Приоритет</span><b>{String(task.priority ?? '—')}</b><span>Спринт</span><b>{String(task.sprint_id ?? '—')}</b><span>Релиз</span><b>{String(task.release_id ?? '—')}</b></div>
        <div className="description-box">{String(task.description ?? 'Описание отсутствует')}</div>
      </div>}
    </aside>
  </>
}

export function OverviewPage() {
  const result = useHarness('Дай обзор и риски')
  const data = (result?.data ?? {}) as Record<string, unknown>
  const risks = Array.isArray(data.risks) ? data.risks as Array<Record<string, unknown>> : []
  return <section className="page">
    <PageHeader title="Обзор" subtitle="Состояние продуктов, риски и точки внимания владельца продукта" />
    <div className="metric-grid"><MetricCard label="Всего задач" value={String(data.tasks_total ?? '—')} /><MetricCard label="В работе" value={String(data.active ?? '—')} /><MetricCard label="Завершено" value={String(data.completed ?? '—')} /><MetricCard label="Заблокировано" value={String(data.blocked ?? '—')} hint="требуют внимания" /></div>
    <div className="content-grid"><div className="panel"><div className="panel-title"><strong>Очередь внимания</strong><span>{risks.length}</span></div>{risks.length ? risks.map(r => <div className="risk-row" key={String(r.key)}><div><b>{String(r.key)}</b><span>{String(r.title ?? '')}</span></div><em>{String(r.status ?? '')}</em></div>) : <div className="muted">Критичные элементы не обнаружены.</div>}</div><div className="panel"><div className="panel-title"><strong>Контур Harness</strong><span className="green-badge">ACTIVE</span></div><div className="fact-row"><span>Runtime</span><b>Harness Core</b></div><div className="fact-row"><span>Adapter</span><b>{String(data.adapter ?? 'fake-as21')}</b></div><div className="fact-row"><span>Evidence</span><b>{result?.evidence.length ?? 0}</b></div><div className="fact-row"><span>Trace</span><b className="mono">{result?.trace_id?.slice(0, 8) ?? '—'}</b></div></div></div>
  </section>
}

export function TasksPage() {
  const [search, setSearch] = useState('login')
  const [submitted, setSubmitted] = useState('login')
  const result = useHarness(`Найди ${submitted}`)
  const data = (result?.data ?? {}) as { tasks?: TaskRow[] }
  const tasks = data.tasks ?? []
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedTask, setSelectedTask] = useState<TaskRow | null>(null)
  const [localTasks, setLocalTasks] = useState<LocalTask[]>(() => {
    try { return JSON.parse(localStorage.getItem('po-local-tasks') ?? '[]') as LocalTask[] } catch { return [] }
  })
  useEffect(() => { localStorage.setItem('po-local-tasks', JSON.stringify(localTasks)) }, [localTasks])
  const allCount = useMemo(() => tasks.length + localTasks.length, [tasks.length, localTasks.length])
  return <section className="page"><PageHeader title="Задачи" subtitle="Поиск, статус, постановка, вложения и task intelligence" />
    <form className="panel toolbar" onSubmit={e => { e.preventDefault(); if (search.trim()) setSubmitted(search.trim()) }}><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Поиск задач" /><button type="submit">Найти</button><button type="button">Фильтры</button><button type="button" onClick={() => setDrawerOpen(true)}>+ Локальная задача</button></form>
    {localTasks.length > 0 && <div className="panel local-panel"><div className="panel-title"><strong>Локальные задачи</strong><span>{localTasks.length}</span></div>{localTasks.map(t => <div className="task-row" key={t.id}><div className="task-key">{t.id}</div><div className="task-main"><b>{t.title}</b><span>{t.owner || 'Без ответственного'}</span></div><div className="status-pill">LOCAL</div></div>)}</div>}
    <div className="panel"><div className="panel-title"><strong>Задачи</strong><span>{allCount}</span></div>{tasks.length ? <div className="task-card-grid">{tasks.map(t => <TaskCard key={String(t.key)} task={t} onOpen={setSelectedTask} />)}</div> : <EmptyData text="Нет данных по задачам" />}</div>
    <LocalTaskDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} onCreate={task => setLocalTasks(items => [task, ...items])} />
    <TaskDetailsDrawer task={selectedTask} onClose={() => setSelectedTask(null)} />
  </section>
}

export function SprintPage() {
  const result = useHarness('Покажи состояние WMB-SPRNT-1'); const d = (result?.data ?? {}) as Record<string, unknown>
  return <section className="page"><PageHeader title="Спринты" subtitle="Velocity, WIP, throughput, predictability и риски" /><div className="metric-grid"><MetricCard label="Scope" value={String(d.total ?? '—')} /><MetricCard label="Completed" value={String(d.completed ?? '—')} /><MetricCard label="Active" value={String(d.active ?? '—')} /><MetricCard label="Готовность" value={`${String(d.completion_percent ?? '—')}%`} /></div><div className="panel"><div className="panel-title"><strong>Текущий спринт</strong><span>{String(d.sprint_id ?? 'WMB-SPRNT-1')}</span></div><div className="muted">Метрики считаются детерминированно. LLM используется только для объяснения.</div></div></section>
}

export function ReleasesPage() {
  const result = useHarness('Риски WMB-2024-Q3'); const d = (result?.data ?? {}) as Record<string, unknown>
  return <section className="page"><PageHeader title="Релизы" subtitle="Готовность, blockers, dependencies, risk queue и forecast inputs" /><div className="metric-grid"><MetricCard label="Scope" value={String(d.total ?? '—')} /><MetricCard label="Completed" value={String(d.completed ?? '—')} /><MetricCard label="Blocked" value={String(d.blocked ?? '—')} /><MetricCard label="Готовность" value={`${String(d.completion_percent ?? '—')}%`} /></div><div className="panel"><div className="panel-title"><strong>{String(d.release_id ?? 'Release')}</strong><span className="green-badge">TRACKED</span></div><div className="muted">Forecast будет активирован только после появления честного исторического baseline.</div></div></section>
}

export function TeamPage() {
  const result = useHarness('Покажи нагрузку команды'); const d = (result?.data ?? {}) as { workload?: Array<Record<string, unknown>> }; const rows = d.workload ?? []
  return <section className="page"><PageHeader title="Команда" subtitle="Нагрузка, WIP, blocked, capacity и распределение" /><div className="panel"><div className="panel-title"><strong>Активная нагрузка</strong><span>{rows.length}</span></div>{rows.length ? rows.map(row => <div className="task-row" key={String(row.member)}><div className="avatar">{String(row.member).slice(0, 1)}</div><div className="task-main"><b>{String(row.member)}</b><span>{String(row.tasks)} задач</span></div><div className="status-pill">{String(row.estimated_hours)} ч</div></div>) : <EmptyData text="Нет данных команды" />}</div></section>
}

export function QualityPage() {
  const result = useHarness('Оцени постановку WMB-102')
  return <section className="page"><PageHeader title="Качество" subtitle="Качество постановки задач и evidence-based проверки" /><div className="panel"><div className="panel-title"><strong>Task Quality</strong><span className="green-badge">DETERMINISTIC</span></div><pre className="json-box">{result ? JSON.stringify(result.data, null, 2) : 'Загрузка…'}</pre></div></section>
}
