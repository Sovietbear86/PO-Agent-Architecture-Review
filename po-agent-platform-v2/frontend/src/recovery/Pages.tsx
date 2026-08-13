import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { agent, HarnessQueryResponse } from '../api/client'

type WorkspaceContext = { openAgent(): void }
type TaskRow = Record<string, unknown>
type LocalTask = { id: string; title: string; description: string; owner: string; createdAt: string }
type FilterMode = 'text' | 'assignee' | 'status' | 'sprint' | 'release'
type IntelligenceMode = 'summary' | 'quality' | 'history' | 'missing'

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

function HarnessMeta({ result }: { result: HarnessQueryResponse | null }) {
  return <div className="filter-status"><span>Skill: {result?.skill?.id ?? '—'}</span><span>Evidence: {result?.evidence.length ?? 0}</span><span>Trace: {result?.trace_id?.slice(0,8) ?? '—'}</span></div>
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

function intelligenceQuery(key: string, mode: IntelligenceMode) {
  if (mode === 'summary') return `Кратко что нужно сделать по задаче ${key}`
  if (mode === 'quality') return `Оцени постановку ${key}`
  if (mode === 'history') return `Покажи историю ${key}`
  return `Чего не хватает в задаче ${key}`
}

function TaskDetailsDrawer({ task, onClose }: { task: TaskRow | null; onClose(): void }) {
  const [mode, setMode] = useState<IntelligenceMode>('summary')
  const key = String(task?.key ?? '')
  const result = useHarness(key ? intelligenceQuery(key, mode) : 'Найди __none__')
  useEffect(() => { setMode('summary') }, [key])
  return <>
    <div className={`drawer-scrim ${task ? 'visible' : ''}`} onClick={onClose} />
    <aside className={`task-drawer ${task ? 'task-drawer-open' : ''}`} aria-hidden={!task}>
      <div className="agent-header"><div><div className="agent-kicker">TASK DETAILS</div><strong>{key}</strong></div><button className="icon-button" onClick={onClose}>×</button></div>
      {task && <div className="task-details">
        <h2>{String(task.title ?? '')}</h2>
        <div className="details-grid"><span>Статус</span><b>{String(task.status ?? '—')}</b><span>Исполнитель</span><b>{String(task.assignee ?? 'Не назначен')}</b><span>Приоритет</span><b>{String(task.priority ?? '—')}</b><span>Спринт</span><b>{String(task.sprint_id ?? '—')}</b><span>Релиз</span><b>{String(task.release_id ?? '—')}</b></div>
        <div className="description-box">{String(task.description ?? 'Описание отсутствует')}</div>
        <div className="intelligence-tabs">
          <button className={mode === 'summary' ? 'active' : ''} onClick={() => setMode('summary')}>Резюме</button>
          <button className={mode === 'quality' ? 'active' : ''} onClick={() => setMode('quality')}>Качество</button>
          <button className={mode === 'missing' ? 'active' : ''} onClick={() => setMode('missing')}>Что не хватает</button>
          <button className={mode === 'history' ? 'active' : ''} onClick={() => setMode('history')}>История</button>
        </div>
        <div className="intelligence-box">
          <div className="intelligence-title"><strong>Task Intelligence</strong>{result?.skill && <span>{result.skill.id}@{result.skill.version}</span>}</div>
          <p>{result?.answer ?? 'Загрузка…'}</p>
          {result?.warnings.length ? <div className="warning">{result.warnings.join(' · ')}</div> : null}
          {result?.data ? <pre className="json-box compact-json">{JSON.stringify(result.data, null, 2)}</pre> : null}
        </div>
      </div>}
    </aside>
  </>
}

function taskQuery(mode: FilterMode, value: string) {
  const v = value.trim()
  if (mode === 'assignee') return `Покажи задачи исполнитель ${v}`
  if (mode === 'status') return `Покажи задачи в статусе ${v}`
  if (mode === 'sprint') return `Покажи задачи спринта ${v}`
  if (mode === 'release') return `Покажи задачи релиза ${v}`
  return `Найди ${v || 'login'}`
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
  const [mode, setMode] = useState<FilterMode>('text')
  const [search, setSearch] = useState('login')
  const [submitted, setSubmitted] = useState({ mode: 'text' as FilterMode, value: 'login' })
  const result = useHarness(taskQuery(submitted.mode, submitted.value))
  const data = (result?.data ?? {}) as { tasks?: TaskRow[] }
  const tasks = data.tasks ?? []
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedTask, setSelectedTask] = useState<TaskRow | null>(null)
  const [localTasks, setLocalTasks] = useState<LocalTask[]>(() => {
    try { return JSON.parse(localStorage.getItem('po-local-tasks') ?? '[]') as LocalTask[] } catch { return [] }
  })
  useEffect(() => { localStorage.setItem('po-local-tasks', JSON.stringify(localTasks)) }, [localTasks])
  const allCount = useMemo(() => tasks.length + localTasks.length, [tasks.length, localTasks.length])
  const placeholder = mode === 'text' ? 'Текст или ключ задачи' : mode === 'assignee' ? 'Ivanov.I.I' : mode === 'status' ? 'In Progress' : mode === 'sprint' ? 'WMB-SPRNT-1' : 'WMB-2024-Q3'
  return <section className="page"><PageHeader title="Задачи" subtitle="Поиск, статус, постановка, вложения и task intelligence" />
    <form className="panel filter-toolbar" onSubmit={e => { e.preventDefault(); if (search.trim()) setSubmitted({ mode, value: search.trim() }) }}>
      <div className="filter-modes">
        {([['text','Текст'],['assignee','Исполнитель'],['status','Статус'],['sprint','Спринт'],['release','Релиз']] as Array<[FilterMode,string]>).map(([id,label]) => <button type="button" key={id} className={mode === id ? 'active' : ''} onClick={() => { setMode(id); setSearch('') }}>{label}</button>)}
      </div>
      <div className="filter-input-row"><input value={search} onChange={e => setSearch(e.target.value)} placeholder={placeholder} /><button type="submit">Найти</button><button type="button" onClick={() => setDrawerOpen(true)}>+ Локальная задача</button></div>
      <HarnessMeta result={result} />
    </form>
    {localTasks.length > 0 && <div className="panel local-panel"><div className="panel-title"><strong>Локальные задачи</strong><span>{localTasks.length}</span></div>{localTasks.map(t => <div className="task-row" key={t.id}><div className="task-key">{t.id}</div><div className="task-main"><b>{t.title}</b><span>{t.owner || 'Без ответственного'}</span></div><div className="status-pill">LOCAL</div></div>)}</div>}
    <div className="panel"><div className="panel-title"><strong>Задачи</strong><span>{allCount}</span></div>{tasks.length ? <div className="task-card-grid">{tasks.map(t => <TaskCard key={String(t.key)} task={t} onOpen={setSelectedTask} />)}</div> : <EmptyData text="Нет данных по задачам" />}</div>
    <LocalTaskDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} onCreate={task => setLocalTasks(items => [task, ...items])} />
    <TaskDetailsDrawer task={selectedTask} onClose={() => setSelectedTask(null)} />
  </section>
}

export function SprintPage() {
  const [sprintId, setSprintId] = useState('WMB-SPRNT-1')
  const [submitted, setSubmitted] = useState('WMB-SPRNT-1')
  const health = useHarness(`Покажи состояние ${submitted}`)
  const velocity = useHarness(`Покажи velocity ${submitted}`)
  const throughput = useHarness(`Покажи throughput ${submitted}`)
  const wip = useHarness(`Покажи WIP ${submitted}`)
  const predictability = useHarness(`Покажи predictability ${submitted}`)
  const risks = useHarness(`Покажи риски спринта ${submitted}`)
  const hd = (health?.data ?? {}) as Record<string, unknown>
  const vd = (velocity?.data ?? {}) as Record<string, unknown>
  const td = (throughput?.data ?? {}) as Record<string, unknown>
  const wd = (wip?.data ?? {}) as Record<string, unknown>
  const pd = (predictability?.data ?? {}) as Record<string, unknown>
  const rd = (risks?.data ?? {}) as { risks?: Array<Record<string, unknown>>; count?: number }
  const riskRows = rd.risks ?? []
  return <section className="page">
    <PageHeader title="Спринты" subtitle="Velocity, throughput, WIP, predictability и очередь рисков" />
    <form className="panel entity-toolbar" onSubmit={e => { e.preventDefault(); if (sprintId.trim()) setSubmitted(sprintId.trim().toUpperCase()) }}><div><span>Спринт</span><input value={sprintId} onChange={e => setSprintId(e.target.value)} /></div><button type="submit">Обновить</button></form>
    <div className="metric-grid"><MetricCard label="Scope" value={String(hd.total ?? '—')} /><MetricCard label="Completed" value={String(hd.completed ?? '—')} /><MetricCard label="Velocity" value={`${String(vd.velocity ?? '—')} ${String(vd.unit ?? '')}`} /><MetricCard label="Predictability" value={`${String(pd.predictability_percent ?? '—')}%`} hint={predictability?.warnings.includes('current_scope_used_as_commitment_baseline') ? 'current scope baseline' : undefined} /></div>
    <div className="insight-grid">
      <div className="panel insight-card"><div className="panel-title"><strong>Throughput</strong><span>{throughput?.skill?.id ?? '—'}</span></div><div className="insight-value">{String(td.throughput_tasks ?? '—')}</div><div className="muted">завершённых задач · unit {String(td.unit ?? 'tasks')}</div><HarnessMeta result={throughput} /></div>
      <div className="panel insight-card"><div className="panel-title"><strong>WIP</strong><span>{wip?.skill?.id ?? '—'}</span></div><div className="insight-value">{String(wd.wip ?? '—')}</div><div className="muted">задач в активной работе</div><HarnessMeta result={wip} /></div>
      <div className="panel insight-card"><div className="panel-title"><strong>Готовность</strong><span>{health?.skill?.id ?? '—'}</span></div><div className="insight-value">{String(hd.completion_percent ?? '—')}%</div><div className="muted">{String(hd.completed ?? '—')} из {String(hd.total ?? '—')} задач</div><HarnessMeta result={health} /></div>
    </div>
    <div className="panel"><div className="panel-title"><strong>Risk Queue</strong><span>{String(rd.count ?? riskRows.length)}</span></div>{riskRows.length ? riskRows.map(row => <div className="risk-row" key={String(row.key)}><div><b>{String(row.key)}</b><span>{String(row.title ?? '')} · {(row.reasons as string[] | undefined)?.join(', ')}</span></div><em>{String(row.risk_score ?? '')}</em></div>) : <div className="muted">Риски не выявлены.</div>}<HarnessMeta result={risks} /></div>
  </section>
}

export function ReleasesPage() {
  const [releaseId, setReleaseId] = useState('WMB-2024-Q3')
  const [submitted, setSubmitted] = useState('WMB-2024-Q3')
  const scope = useHarness(`Покажи scope ${submitted}`)
  const progress = useHarness(`Покажи прогресс ${submitted}`)
  const blockers = useHarness(`Покажи блокеры ${submitted}`)
  const dependencies = useHarness(`Покажи зависимости ${submitted}`)
  const risks = useHarness(`Покажи риски релиза ${submitted}`)
  const sd = (scope?.data ?? {}) as { count?: number; tasks?: TaskRow[] }
  const pd = (progress?.data ?? {}) as Record<string, unknown>
  const bd = (blockers?.data ?? {}) as { count?: number; tasks?: TaskRow[] }
  const dd = (dependencies?.data ?? {}) as { internal?: Array<Record<string, unknown>>; external?: Array<Record<string, unknown>> }
  const rd = (risks?.data ?? {}) as { risk_queue?: Array<Record<string, unknown>> }
  const riskRows = rd.risk_queue ?? []
  return <section className="page">
    <PageHeader title="Релизы" subtitle="Progress, blockers, dependencies и deterministic risk queue" />
    <form className="panel entity-toolbar" onSubmit={e => { e.preventDefault(); if (releaseId.trim()) setSubmitted(releaseId.trim().toUpperCase()) }}><div><span>Релиз</span><input value={releaseId} onChange={e => setReleaseId(e.target.value)} /></div><button type="submit">Обновить</button></form>
    <div className="metric-grid"><MetricCard label="Scope" value={String(sd.count ?? '—')} /><MetricCard label="Completed" value={String(pd.completed ?? '—')} /><MetricCard label="Blocked" value={String(pd.blocked ?? '—')} /><MetricCard label="Готовность" value={`${String(pd.task_completion_percent ?? '—')}%`} hint={pd.effort_completion_percent != null ? `effort ${String(pd.effort_completion_percent)}%` : undefined} /></div>
    <div className="content-grid"><div className="panel"><div className="panel-title"><strong>Очередь рисков релиза</strong><span>{riskRows.length}</span></div>{riskRows.length ? riskRows.map((row, index) => { const task = (row.task ?? {}) as TaskRow; return <div className="risk-row" key={String(task.key ?? index)}><div><b>{String(task.key ?? '')}</b><span>{String(task.title ?? '')} · {((row.reasons ?? []) as string[]).join(', ')}</span></div><em>{String(row.risk_score ?? '')}</em></div> }) : <div className="muted">Риски не выявлены.</div>}<HarnessMeta result={risks} /></div>
      <div className="panel"><div className="panel-title"><strong>Dependencies</strong><span>{(dd.internal?.length ?? 0) + (dd.external?.length ?? 0)}</span></div><div className="fact-row"><span>Внутренние</span><b>{dd.internal?.length ?? 0}</b></div><div className="fact-row"><span>Внешние</span><b>{dd.external?.length ?? 0}</b></div><HarnessMeta result={dependencies} /></div></div>
    <div className="panel"><div className="panel-title"><strong>Blockers</strong><span>{bd.count ?? 0}</span></div>{bd.tasks?.length ? bd.tasks.map(task => <div className="task-row" key={String(task.key)}><div className="task-key">{String(task.key)}</div><div className="task-main"><b>{String(task.title ?? '')}</b><span>{String(task.assignee ?? 'Не назначен')}</span></div><div className="status-pill">{String(task.status ?? '')}</div></div>) : <div className="muted">Заблокированных задач нет.</div>}<HarnessMeta result={blockers} /></div>
    <div className="form-note release-note">Forecast не активирован: master-spec требует честный исторический baseline. До появления source data UI не показывает псевдопрогноз.</div>
  </section>
}

export function TeamPage() {
  const result = useHarness('Покажи нагрузку команды'); const d = (result?.data ?? {}) as { workload?: Array<Record<string, unknown>> }; const rows = d.workload ?? []
  return <section className="page"><PageHeader title="Команда" subtitle="Нагрузка, WIP, blocked, capacity и распределение" /><div className="panel"><div className="panel-title"><strong>Активная нагрузка</strong><span>{rows.length}</span></div>{rows.length ? rows.map(row => <div className="task-row" key={String(row.member)}><div className="avatar">{String(row.member).slice(0, 1)}</div><div className="task-main"><b>{String(row.member)}</b><span>{String(row.tasks)} задач</span></div><div className="status-pill">{String(row.estimated_hours)} ч</div></div>) : <EmptyData text="Нет данных команды" />}</div></section>
}

export function QualityPage() {
  const result = useHarness('Оцени постановку WMB-102')
  return <section className="page"><PageHeader title="Качество" subtitle="Качество постановки задач и evidence-based проверки" /><div className="panel"><div className="panel-title"><strong>Task Quality</strong><span className="green-badge">DETERMINISTIC</span></div><pre className="json-box">{result ? JSON.stringify(result.data, null, 2) : 'Загрузка…'}</pre></div></section>
}
