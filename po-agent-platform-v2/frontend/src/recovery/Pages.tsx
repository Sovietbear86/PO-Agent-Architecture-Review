import { FormEvent, ReactNode, useEffect, useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { agent, HarnessQueryResponse } from '../api/client'
import { ResultStatePanel } from '../components/ResultStatePanel'
import { classifyResult, getCapabilityData, stateAllowsBusinessData } from './resultState'
import { SnapshotRefresh, useSnapshotHarness } from './pageSnapshot'

type WorkspaceContext = { openAgent(): void }
type TaskRow = Record<string, unknown>
type LocalTask = {
  id: string
  title: string
  description: string
  owner: string
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  status: 'TODO' | 'IN_PROGRESS' | 'BLOCKED' | 'DONE'
  labels: string[]
  createdAt: string
}
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

function PageHeader({ title, subtitle, extra }: { title: string; subtitle: string; extra?: ReactNode }) {
  const { openAgent } = useOutletContext<WorkspaceContext>()
  return <div className="page-heading"><div><h1>{title}</h1><p>{subtitle}</p></div><div className="page-heading-actions">{extra}<button className="primary-button" onClick={openAgent}>Спросить PO Agent</button></div></div>
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
  const [priority, setPriority] = useState<LocalTask['priority']>('MEDIUM')
  const [status, setStatus] = useState<LocalTask['status']>('TODO')
  const [labels, setLabels] = useState('')
  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!title.trim()) return
    onCreate({
      id: `LOCAL-${Date.now()}`,
      title: title.trim(),
      description: description.trim(),
      owner: owner.trim(),
      priority,
      status,
      labels: labels.split(',').map(item => item.trim()).filter(Boolean),
      createdAt: new Date().toISOString(),
    })
    setTitle(''); setDescription(''); setOwner(''); setPriority('MEDIUM'); setStatus('TODO'); setLabels(''); onClose()
  }
  return <>
    <div className={`drawer-scrim ${open ? 'visible' : ''}`} onClick={onClose} />
    <aside className={`task-drawer ${open ? 'task-drawer-open' : ''}`} aria-hidden={!open}>
      <div className="agent-header"><div><div className="agent-kicker">LOCAL TASK</div><strong>Создать локальную задачу</strong></div><button className="icon-button" onClick={onClose}>×</button></div>
      <form className="task-form" onSubmit={submit}>
        <label>Название<input value={title} onChange={e => setTitle(e.target.value)} placeholder="Что нужно сделать" autoFocus={open} /></label>
        <label>Описание<textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Контекст, ожидаемый результат, ограничения" rows={7} /></label>
        <label>Ответственный<input value={owner} onChange={e => setOwner(e.target.value)} placeholder="Опционально" /></label>
        <label>Приоритет<select value={priority} onChange={e => setPriority(e.target.value as LocalTask['priority'])}><option value="LOW">LOW</option><option value="MEDIUM">MEDIUM</option><option value="HIGH">HIGH</option><option value="CRITICAL">CRITICAL</option></select></label>
        <label>Статус<select value={status} onChange={e => setStatus(e.target.value as LocalTask['status'])}><option value="TODO">TODO</option><option value="IN_PROGRESS">IN PROGRESS</option><option value="BLOCKED">BLOCKED</option><option value="DONE">DONE</option></select></label>
        <label>Метки<input value={labels} onChange={e => setLabels(e.target.value)} placeholder="через запятую" /></label>
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
  const [refreshNonce, setRefreshNonce] = useState(0)
  const resultQ = useSnapshotHarness('tasks:' + submitted.mode + ':' + submitted.value, taskQuery(submitted.mode, submitted.value), refreshNonce)
  const result = resultQ.result
  const data = getCapabilityData(result) as { tasks?: TaskRow[] }
  const tasks = data.tasks ?? []
  const resultState = classifyResult(result)
  const [as21StatusFilter, setAs21StatusFilter] = useState('ALL')
  const [localStatusFilter, setLocalStatusFilter] = useState<'ALL' | LocalTask['status']>('ALL')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedTask, setSelectedTask] = useState<TaskRow | null>(null)
  const [localTasks, setLocalTasks] = useState<LocalTask[]>(() => {
    try {
      const raw = JSON.parse(localStorage.getItem('po-local-tasks') ?? '[]') as Array<Partial<LocalTask>>
      return raw.map(task => ({
        id: String(task.id ?? `LOCAL-${Date.now()}`),
        title: String(task.title ?? ''),
        description: String(task.description ?? ''),
        owner: String(task.owner ?? ''),
        priority: task.priority ?? 'MEDIUM',
        status: task.status ?? 'TODO',
        labels: Array.isArray(task.labels) ? task.labels : [],
        createdAt: String(task.createdAt ?? new Date().toISOString()),
      }))
    } catch { return [] }
  })
  useEffect(() => { localStorage.setItem('po-local-tasks', JSON.stringify(localTasks)) }, [localTasks])
  const as21Statuses = useMemo(() => Array.from(new Set(tasks.map(task => String(task.status ?? '').trim()).filter(Boolean))).sort(), [tasks])
  const visibleTasks = useMemo(
    () => as21StatusFilter === 'ALL' ? tasks : tasks.filter(task => String(task.status ?? '').toLocaleLowerCase() === as21StatusFilter.toLocaleLowerCase()),
    [tasks, as21StatusFilter],
  )
  const visibleLocalTasks = useMemo(
    () => localStatusFilter === 'ALL' ? localTasks : localTasks.filter(task => task.status === localStatusFilter),
    [localTasks, localStatusFilter],
  )
  const placeholder = mode === 'text' ? 'Текст или ключ задачи' : mode === 'assignee' ? 'Ivanov.I.I' : mode === 'status' ? 'In Progress' : mode === 'sprint' ? 'WMB-SPRNT-1' : 'WMB-2024-Q3'
  return <section className="page page-tasks"><PageHeader title="Задачи" subtitle="Поиск, статус, постановка, вложения и task intelligence" extra={<SnapshotRefresh updatedAt={[resultQ.updatedAt]} refreshing={resultQ.refreshing} refreshError={resultQ.refreshError} onRefresh={() => setRefreshNonce(value => value + 1)} />} />
    <form className="panel filter-toolbar" onSubmit={e => { e.preventDefault(); if (search.trim()) setSubmitted({ mode, value: search.trim() }) }}>
      <div className="filter-modes">
        {([['text','Текст'],['assignee','Исполнитель'],['status','Статус'],['sprint','Спринт'],['release','Релиз']] as Array<[FilterMode,string]>).map(([id,label]) => <button type="button" key={id} className={mode === id ? 'active' : ''} onClick={() => { setMode(id); setSearch('') }}>{label}</button>)}
      </div>
      <div className="filter-input-row"><input value={search} onChange={e => setSearch(e.target.value)} placeholder={placeholder} /><button type="submit">Найти</button><button type="button" onClick={() => setDrawerOpen(true)}>+ Локальная задача</button></div>
      <div className="filter-input-row">
        <label>Статус AS21
          <select value={as21StatusFilter} onChange={e => setAs21StatusFilter(e.target.value)}>
            <option value="ALL">Все</option>
            {as21Statuses.map(status => <option key={status} value={status}>{status}</option>)}
          </select>
        </label>
        <label>Статус локальных
          <select value={localStatusFilter} onChange={e => setLocalStatusFilter(e.target.value as 'ALL' | LocalTask['status'])}>
            <option value="ALL">Все</option>
            <option value="TODO">TODO</option>
            <option value="IN_PROGRESS">IN PROGRESS</option>
            <option value="BLOCKED">BLOCKED</option>
            <option value="DONE">DONE</option>
          </select>
        </label>
      </div>
      <HarnessMeta result={result} />
    </form>
    {localTasks.length > 0 && <div className="panel local-panel">
      <div className="panel-title"><strong>Локальные задачи</strong><span>{visibleLocalTasks.length}/{localTasks.length}</span></div>
      {visibleLocalTasks.map(t => <div className="task-row" key={t.id}>
        <div className="task-key">{t.id}</div>
        <div className="task-main">
          <b>{t.title}</b>
          <span>{t.owner || 'Без ответственного'} · {t.priority}{t.labels.length ? ` · ${t.labels.join(', ')}` : ''}</span>
        </div>
        <select
          className="status-pill"
          value={t.status}
          onChange={e => setLocalTasks(items => items.map(item => item.id === t.id ? { ...item, status: e.target.value as LocalTask['status'] } : item))}
          aria-label={`Статус ${t.id}`}
        >
          <option value="TODO">TODO</option>
          <option value="IN_PROGRESS">IN PROGRESS</option>
          <option value="BLOCKED">BLOCKED</option>
          <option value="DONE">DONE</option>
        </select>
        <button
          type="button"
          className="icon-button"
          aria-label={`Удалить ${t.id}`}
          onClick={() => setLocalTasks(items => items.filter(item => item.id !== t.id))}
        >×</button>
      </div>)}
    </div>}
    <div className="panel"><div className="panel-title"><strong>Задачи AS21</strong><span>{stateAllowsBusinessData(resultState) ? `${visibleTasks.length}/${tasks.length}` : '—'}</span></div>{stateAllowsBusinessData(resultState) ? (tasks.length ? (visibleTasks.length ? <div className="task-card-grid">{visibleTasks.map(t => <TaskCard key={String(t.key)} task={t} onOpen={setSelectedTask} />)}</div> : <EmptyData text="По выбранному статусу задач нет" />) : <EmptyData text="Источник подтвердил: задачи не найдены" />) : <ResultStatePanel result={result} />}</div>
    <LocalTaskDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} onCreate={task => setLocalTasks(items => [task, ...items])} />
    <TaskDetailsDrawer task={selectedTask} onClose={() => setSelectedTask(null)} />
  </section>
}

export function SprintPage() {
  const [sprintId, setSprintId] = useState('WMB-SPRNT-1')
  const [submitted, setSubmitted] = useState('WMB-SPRNT-1')
  const [refreshNonce, setRefreshNonce] = useState(0)
  const healthQ = useSnapshotHarness('sprint:' + submitted, `Покажи состояние ${submitted}`, refreshNonce)
  const velocityQ = useSnapshotHarness('sprint:' + submitted, `Покажи velocity ${submitted}`, refreshNonce)
  const throughputQ = useSnapshotHarness('sprint:' + submitted, `Покажи throughput ${submitted}`, refreshNonce)
  const wipQ = useSnapshotHarness('sprint:' + submitted, `Покажи WIP ${submitted}`, refreshNonce)
  const predictabilityQ = useSnapshotHarness('sprint:' + submitted, `Покажи predictability ${submitted}`, refreshNonce)
  const risksQ = useSnapshotHarness('sprint:' + submitted, `Покажи риски спринта ${submitted}`, refreshNonce)
  const health = healthQ.result
  const velocity = velocityQ.result
  const throughput = throughputQ.result
  const wip = wipQ.result
  const predictability = predictabilityQ.result
  const risks = risksQ.result
  const hd = getCapabilityData(health) as Record<string, unknown>
  const vd = getCapabilityData(velocity) as Record<string, unknown>
  const td = getCapabilityData(throughput) as Record<string, unknown>
  const wd = getCapabilityData(wip) as Record<string, unknown>
  const pd = getCapabilityData(predictability) as Record<string, unknown>
  const rd = getCapabilityData(risks) as { queue?: Array<Record<string, unknown>>; count?: number }
  const riskRows = rd.queue ?? []
  const healthState = classifyResult(health)
  const velocityState = classifyResult(velocity)
  const throughputState = classifyResult(throughput)
  const wipState = classifyResult(wip)
  const predictabilityState = classifyResult(predictability)
  const risksState = classifyResult(risks)
  return <section className="page page-sprint">
    <PageHeader title="Спринты" subtitle="Velocity, throughput, WIP, predictability и очередь рисков" extra={<SnapshotRefresh updatedAt={[healthQ.updatedAt, velocityQ.updatedAt, throughputQ.updatedAt, wipQ.updatedAt, predictabilityQ.updatedAt, risksQ.updatedAt]} refreshing={healthQ.refreshing || velocityQ.refreshing || throughputQ.refreshing || wipQ.refreshing || predictabilityQ.refreshing || risksQ.refreshing} refreshError={healthQ.refreshError || velocityQ.refreshError || throughputQ.refreshError || wipQ.refreshError || predictabilityQ.refreshError || risksQ.refreshError} onRefresh={() => setRefreshNonce(value => value + 1)} />} />
    <form className="panel entity-toolbar" onSubmit={e => { e.preventDefault(); if (sprintId.trim()) setSubmitted(sprintId.trim().toUpperCase()) }}><div><span>Спринт</span><input value={sprintId} onChange={e => setSprintId(e.target.value)} /></div><button type="submit">Обновить</button></form>
    <div className="metric-grid"><MetricCard label="Scope" value={stateAllowsBusinessData(healthState) ? String(hd.total ?? '—') : '—'} /><MetricCard label="Completed" value={stateAllowsBusinessData(healthState) ? String(hd.completed ?? '—') : '—'} /><MetricCard label="Velocity" value={stateAllowsBusinessData(velocityState) ? `${String(vd.velocity ?? '—')} ${String(vd.unit ?? '')}` : '—'} /><MetricCard label="Predictability" value={stateAllowsBusinessData(predictabilityState) ? `${String(pd.predictability_percent ?? '—')}%` : '—'} hint={stateAllowsBusinessData(predictabilityState) ? (predictability?.warnings.includes('current_scope_used_as_commitment_baseline') ? 'current scope baseline' : undefined) : 'нужен source-backed baseline старта спринта'} /></div>
    <div className="insight-grid">
      <div className="panel insight-card"><div className="panel-title"><strong>Throughput</strong><span>{throughput?.skill?.id ?? '—'}</span></div>{stateAllowsBusinessData(throughputState) ? <><div className="insight-value">{String(td.throughput ?? '—')}</div><div className="muted">завершённых задач · unit {String(td.unit ?? 'tasks')}</div></> : <ResultStatePanel result={throughput} compact />}<HarnessMeta result={throughput} /></div>
      <div className="panel insight-card"><div className="panel-title"><strong>WIP</strong><span>{wip?.skill?.id ?? '—'}</span></div>{stateAllowsBusinessData(wipState) ? <><div className="insight-value">{String(wd.wip ?? '—')}</div><div className="muted">задач в активной работе</div></> : <ResultStatePanel result={wip} compact />}<HarnessMeta result={wip} /></div>
      <div className="panel insight-card"><div className="panel-title"><strong>Готовность</strong><span>{health?.skill?.id ?? '—'}</span></div>{stateAllowsBusinessData(healthState) ? <><div className="insight-value">{String(hd.completion_percent ?? '—')}%</div><div className="muted">{String(hd.completed ?? '—')} из {String(hd.total ?? '—')} задач</div></> : <ResultStatePanel result={health} compact />}<HarnessMeta result={health} /></div>
    </div>
    <div className="panel"><div className="panel-title"><strong>Risk Queue</strong><span>{stateAllowsBusinessData(risksState) ? String(rd.count ?? riskRows.length) : '—'}</span></div>{stateAllowsBusinessData(risksState) ? (riskRows.length ? riskRows.map(row => <div className="risk-row" key={String(row.task_key)}><div><b>{String(row.task_key)}</b><span>{String(row.title ?? '')} · {(row.reasons as string[] | undefined)?.join(', ')}</span></div><em>{String(row.rank ?? '')}</em></div>) : <div className="muted">Источник подтвердил: риски не выявлены.</div>) : <ResultStatePanel result={risks} compact />}<HarnessMeta result={risks} /></div>
  </section>
}

export function ReleasesPage() {
  const [releaseId, setReleaseId] = useState('WMB-2024-Q3')
  const [submitted, setSubmitted] = useState('WMB-2024-Q3')
  const [refreshNonce, setRefreshNonce] = useState(0)
  const scopeQ = useSnapshotHarness('release:' + submitted, `Покажи scope ${submitted}`, refreshNonce)
  const progressQ = useSnapshotHarness('release:' + submitted, `Покажи прогресс ${submitted}`, refreshNonce)
  const blockersQ = useSnapshotHarness('release:' + submitted, `Покажи блокеры ${submitted}`, refreshNonce)
  const dependenciesQ = useSnapshotHarness('release:' + submitted, `Покажи зависимости ${submitted}`, refreshNonce)
  const risksQ = useSnapshotHarness('release:' + submitted, `Покажи риски релиза ${submitted}`, refreshNonce)
  const scope = scopeQ.result
  const progress = progressQ.result
  const blockers = blockersQ.result
  const dependencies = dependenciesQ.result
  const risks = risksQ.result
  const sd = getCapabilityData(scope) as { count?: number; tasks?: TaskRow[] }
  const pd = getCapabilityData(progress) as Record<string, unknown>
  const bd = getCapabilityData(blockers) as { count?: number; tasks?: TaskRow[] }
  const dd = getCapabilityData(dependencies) as { internal?: Array<Record<string, unknown>>; external?: Array<Record<string, unknown>> }
  const rd = getCapabilityData(risks) as { risk_queue?: Array<Record<string, unknown>> }
  const riskRows = rd.risk_queue ?? []
  const scopeState = classifyResult(scope)
  const progressState = classifyResult(progress)
  const blockersState = classifyResult(blockers)
  const dependenciesState = classifyResult(dependencies)
  const releaseRisksState = classifyResult(risks)
  return <section className="page page-releases">
    <PageHeader title="Релизы" subtitle="Progress, blockers, dependencies и deterministic risk queue" extra={<SnapshotRefresh updatedAt={[scopeQ.updatedAt, progressQ.updatedAt, blockersQ.updatedAt, dependenciesQ.updatedAt, risksQ.updatedAt]} refreshing={scopeQ.refreshing || progressQ.refreshing || blockersQ.refreshing || dependenciesQ.refreshing || risksQ.refreshing} refreshError={scopeQ.refreshError || progressQ.refreshError || blockersQ.refreshError || dependenciesQ.refreshError || risksQ.refreshError} onRefresh={() => setRefreshNonce(value => value + 1)} />} />
    <form className="panel entity-toolbar" onSubmit={e => { e.preventDefault(); if (releaseId.trim()) setSubmitted(releaseId.trim().toUpperCase()) }}><div><span>Релиз</span><input value={releaseId} onChange={e => setReleaseId(e.target.value)} /></div><button type="submit">Обновить</button></form>
    <div className="metric-grid"><MetricCard label="Scope" value={stateAllowsBusinessData(scopeState) ? String(sd.count ?? '—') : '—'} /><MetricCard label="Completed" value={stateAllowsBusinessData(progressState) ? String(pd.completed ?? '—') : '—'} /><MetricCard label="Blocked" value={stateAllowsBusinessData(progressState) ? String(pd.blocked ?? '—') : '—'} /><MetricCard label="Готовность" value={stateAllowsBusinessData(progressState) ? `${String(pd.task_completion_percent ?? '—')}%` : '—'} hint={stateAllowsBusinessData(progressState) && pd.effort_completion_percent != null ? `effort ${String(pd.effort_completion_percent)}%` : undefined} /></div>
    <div className="content-grid"><div className="panel"><div className="panel-title"><strong>Очередь рисков релиза</strong><span>{stateAllowsBusinessData(releaseRisksState) ? riskRows.length : '—'}</span></div>{stateAllowsBusinessData(releaseRisksState) ? (riskRows.length ? riskRows.map((row, index) => { const task = (row.task ?? {}) as TaskRow; return <div className="risk-row" key={String(task.key ?? index)}><div><b>{String(task.key ?? '')}</b><span>{String(task.title ?? '')} · {((row.reasons ?? []) as string[]).join(', ')}</span></div><em>{String(row.risk_score ?? '')}</em></div> }) : <div className="muted">Источник подтвердил: риски не выявлены.</div>) : <ResultStatePanel result={risks} compact />}<HarnessMeta result={risks} /></div>
      <div className="panel"><div className="panel-title"><strong>Dependencies</strong><span>{stateAllowsBusinessData(dependenciesState) ? (dd.internal?.length ?? 0) + (dd.external?.length ?? 0) : '—'}</span></div>{stateAllowsBusinessData(dependenciesState) ? <><div className="fact-row"><span>Внутренние</span><b>{dd.internal?.length ?? 0}</b></div><div className="fact-row"><span>Внешние</span><b>{dd.external?.length ?? 0}</b></div></> : <ResultStatePanel result={dependencies} compact />}<HarnessMeta result={dependencies} /></div></div>
    <div className="panel"><div className="panel-title"><strong>Blockers</strong><span>{stateAllowsBusinessData(blockersState) ? (bd.count ?? '—') : '—'}</span></div>{stateAllowsBusinessData(blockersState) ? (bd.tasks?.length ? bd.tasks.map(task => <div className="task-row" key={String(task.key)}><div className="task-key">{String(task.key)}</div><div className="task-main"><b>{String(task.title ?? '')}</b><span>{String(task.assignee ?? 'Не назначен')}</span></div><div className="status-pill">{String(task.status ?? '')}</div></div>) : <div className="muted">Источник подтвердил: заблокированных задач нет.</div>) : <ResultStatePanel result={blockers} compact />}<HarnessMeta result={blockers} /></div>
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
