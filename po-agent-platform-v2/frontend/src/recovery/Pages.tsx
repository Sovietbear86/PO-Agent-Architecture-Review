import { FormEvent, ReactNode, useEffect, useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { agent, HarnessQueryResponse } from '../api/client'
import { ResultStatePanel } from '../components/ResultStatePanel'
import { RichAnswer } from '../components/agent/RichAnswer'
import { classifyResult, getCapabilityData, stateAllowsBusinessData } from './resultState'
import { SnapshotRefresh, SnapshotStatus, useSessionState, useSnapshotHarness } from './pageSnapshot'

type WorkspaceContext = { openAgent(): void }
type TaskRow = Record<string, unknown>
type LocalTask = {
  id: string
  number: number
  title: string
  description: string
  owner: string
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  status: 'TODO' | 'IN_PROGRESS' | 'BLOCKED' | 'DONE'
  labels: string[]
  deadline: string
  createdAt: string
}
type IntelligenceMode = 'summary' | 'quality' | 'history' | 'missing'

function useHarness(query: string, enabled = true) {
  const [result, setResult] = useState<HarnessQueryResponse | null>(null)
  useEffect(() => {
    if (!enabled || !query.trim()) {
      setResult(null)
      return
    }
    let alive = true
    agent.query({ query }).then(r => alive && setResult(r)).catch(() => alive && setResult(null))
    return () => { alive = false }
  }, [query, enabled])
  return result
}

function useHarnessRequest(query: string, enabled = true) {
  const [result, setResult] = useState<HarnessQueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!enabled || !query.trim()) {
      setResult(null)
      setLoading(false)
      setError(false)
      return
    }

    let alive = true
    setResult(null)
    setLoading(true)
    setError(false)

    agent.query({ query })
      .then(response => {
        if (!alive) return
        setResult(response)
        setLoading(false)
      })
      .catch(() => {
        if (!alive) return
        setResult(null)
        setLoading(false)
        setError(true)
      })

    return () => { alive = false }
  }, [query, enabled])

  return { result, loading, error }
}


function MetricCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</div>
}

function PageHeader({ title, subtitle, extra }: { title: string; subtitle: string; extra?: ReactNode }) {
  const { openAgent } = useOutletContext<WorkspaceContext>()
  return <div className="page-heading"><div><h1>{title}</h1><p>{subtitle}</p></div><div className="page-heading-actions">{extra}<button className="primary-button" onClick={openAgent}>Спросить PO Agent</button></div></div>
}

function priorityLabel(value: LocalTask['priority']) {
  return value === 'LOW' ? 'Низкий' : value === 'MEDIUM' ? 'Средний' : value === 'HIGH' ? 'Высокий' : 'Критичный'
}

function localTaskCode(number: number) {
  return `LOCAL-${String(number).padStart(4, '0')}`
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

const INTELLIGENCE_HIDDEN_KEYS = new Set([
  '_agent_core_v4',
  'trajectory',
  'source_data',
  'raw',
  'raw_data',
])

function intelligenceLabel(key: string) {
  const labels: Record<string, string> = {
    task_key: 'Задача',
    title: 'Название',
    description: 'Описание',
    status: 'Статус',
    assignee: 'Исполнитель',
    priority: 'Приоритет',
    score: 'Оценка',
    quality_score: 'Оценка качества',
    issues: 'Замечания',
    warnings: 'Предупреждения',
    recommendations: 'Рекомендации',
    missing: 'Что не хватает',
    history: 'История',
    created_at: 'Создано',
    updated_at: 'Обновлено',
    deadline: 'Дедлайн',
    author: 'Автор',
    from: 'Было',
    to: 'Стало',
    date: 'Дата',
    field: 'Поле',
    comment: 'Комментарий',
  }
  return labels[key] ?? key.split('_').join(' ')
}

function intelligenceScalar(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? 'Да' : 'Нет'
  return String(value)
}

function intelligenceEntries(value: Record<string, unknown>) {
  return Object.entries(value).filter(([key]) =>
    !INTELLIGENCE_HIDDEN_KEYS.has(key) &&
    !key.startsWith('_')
  )
}

function IntelligenceStructuredData({ data }: { data: Record<string, unknown> }) {
  const entries = intelligenceEntries(data)
  if (!entries.length) return null

  const scalarRows = entries.filter(([, value]) =>
    value === null || value === undefined || ['string', 'number', 'boolean'].includes(typeof value)
  )
  const complexRows = entries.filter(([, value]) =>
    !(value === null || value === undefined || ['string', 'number', 'boolean'].includes(typeof value))
  )

  return <div className="intelligence-structured">
    {scalarRows.length > 0 && <div className="answer-table-wrap intelligence-table-wrap">
      <table className="answer-table intelligence-table">
        <tbody>
          {scalarRows.map(([key, value]) => <tr key={key}>
            <th>{intelligenceLabel(key)}</th>
            <td>{intelligenceScalar(value)}</td>
          </tr>)}
        </tbody>
      </table>
    </div>}

    {complexRows.map(([key, value]) => {
      if (Array.isArray(value)) {
        if (!value.length) return null
        const objectRows = value.filter(item => item && typeof item === 'object' && !Array.isArray(item)) as Array<Record<string, unknown>>
        if (objectRows.length === value.length) {
          const columns = Array.from(new Set(objectRows.flatMap(row => intelligenceEntries(row).map(([column]) => column)))).slice(0, 8)
          return <div className="intelligence-section" key={key}>
            <strong>{intelligenceLabel(key)}</strong>
            <div className="answer-table-wrap intelligence-table-wrap">
              <table className="answer-table intelligence-table">
                <thead><tr>{columns.map(column => <th key={column}>{intelligenceLabel(column)}</th>)}</tr></thead>
                <tbody>{objectRows.slice(0, 30).map((row, index) => <tr key={index}>
                  {columns.map(column => <td key={column}>{intelligenceScalar(row[column])}</td>)}
                </tr>)}</tbody>
              </table>
            </div>
            {objectRows.length > 30 && <div className="muted">Показано 30 из {objectRows.length} строк.</div>}
          </div>
        }

        return <div className="intelligence-section" key={key}>
          <strong>{intelligenceLabel(key)}</strong>
          <ul className="answer-list">{value.slice(0, 30).map((item, index) => <li key={index}>{intelligenceScalar(item)}</li>)}</ul>
        </div>
      }

      if (value && typeof value === 'object') {
        return <div className="intelligence-section" key={key}>
          <strong>{intelligenceLabel(key)}</strong>
          <IntelligenceStructuredData data={value as Record<string, unknown>} />
        </div>
      }

      return null
    })}
  </div>
}

function LocalTaskDrawer({
  open,
  onClose,
  task,
  nextNumber,
  onSave,
}: {
  open: boolean
  onClose(): void
  task: LocalTask | null
  nextNumber: number
  onSave(task: LocalTask): void
}) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [owner, setOwner] = useState('')
  const [priority, setPriority] = useState<LocalTask['priority']>('MEDIUM')
  const [status, setStatus] = useState<LocalTask['status']>('TODO')
  const [labels, setLabels] = useState('')
  const [deadline, setDeadline] = useState('')

  useEffect(() => {
    document.body.classList.toggle('task-drawer-active', open)
    return () => document.body.classList.remove('task-drawer-active')
  }, [open])

  useEffect(() => {
    if (!open) return
    setTitle(task?.title ?? '')
    setDescription(task?.description ?? '')
    setOwner(task?.owner ?? '')
    setPriority(task?.priority ?? 'MEDIUM')
    setStatus(task?.status ?? 'TODO')
    setLabels(task?.labels.join(', ') ?? '')
    setDeadline(task?.deadline ?? '')
  }, [open, task])

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (!title.trim()) return
    onSave({
      id: task?.id ?? `LOCAL-${Date.now()}`,
      number: task?.number ?? nextNumber,
      title: title.trim(),
      description: description.trim(),
      owner: owner.trim(),
      priority,
      status,
      labels: labels.split(',').map(item => item.trim()).filter(Boolean),
      deadline,
      createdAt: task?.createdAt ?? new Date().toISOString(),
    })
    onClose()
  }

  const addTag = (tag: string) => {
    const existing = labels.split(',').map(item => item.trim()).filter(Boolean)
    if (!existing.includes(tag)) setLabels([...existing, tag].join(', '))
  }

  return <>
    <div className={`drawer-scrim ${open ? 'visible' : ''}`} onClick={onClose} />
    <aside className={`task-drawer ${open ? 'task-drawer-open' : ''}`} aria-hidden={!open}>
      <div className="agent-header">
        <div>
          <div className="agent-kicker">{localTaskCode(task?.number ?? nextNumber)}</div>
          <strong>{task ? 'Редактировать локальную задачу' : 'Создать локальную задачу'}</strong>
        </div>
        <button className="icon-button" onClick={onClose}>×</button>
      </div>
      <form className="task-form" onSubmit={submit}>
        <label>Название<input value={title} onChange={e => setTitle(e.target.value)} placeholder="Что нужно сделать" autoFocus={open} /></label>
        <label>Описание<textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Контекст, ожидаемый результат, ограничения" rows={7} /></label>
        <label>Ответственный<input value={owner} onChange={e => setOwner(e.target.value)} placeholder="Опционально" /></label>
        <label>Приоритет<select value={priority} onChange={e => setPriority(e.target.value as LocalTask['priority'])}><option value="LOW">Низкий</option><option value="MEDIUM">Средний</option><option value="HIGH">Высокий</option><option value="CRITICAL">Критичный</option></select></label>
        <label>Статус<select value={status} onChange={e => setStatus(e.target.value as LocalTask['status'])}><option value="TODO">TODO</option><option value="IN_PROGRESS">IN PROGRESS</option><option value="BLOCKED">BLOCKED</option><option value="DONE">DONE</option></select></label>
        <label>Теги<input value={labels} onChange={e => setLabels(e.target.value)} placeholder="Управленческие задачи, Поручения — через запятую" /></label>
        <div className="tag-suggestions">
          <button type="button" onClick={() => addTag('Управленческие задачи')}>+ Управленческие задачи</button>
          <button type="button" onClick={() => addTag('Поручения')}>+ Поручения</button>
        </div>
        <label>Дедлайн<input className="deadline-input" type="date" value={deadline} onChange={e => setDeadline(e.target.value)} /></label>
        <div className="form-note">Локальная задача сохраняется только в браузере и не пишет в AS21 без отдельного approval/write capability.</div>
        <div className="form-actions"><button type="button" onClick={onClose}>Отмена</button><button className="primary-button" type="submit" disabled={!title.trim()}>{task ? 'Сохранить' : 'Создать'}</button></div>
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
  const detailQ = useHarnessRequest(key ? `Покажи задачу ${key}` : '', Boolean(key))
  const intelligenceQ = useHarnessRequest(key ? intelligenceQuery(key, mode) : '', Boolean(key))
  const result = intelligenceQ.result
  const exactTaskData = getCapabilityData(detailQ.result)
  const exactTask = (
    exactTaskData.task && typeof exactTaskData.task === 'object' && !Array.isArray(exactTaskData.task)
      ? exactTaskData.task
      : null
  ) as TaskRow | null
  const displayTask = exactTask ?? task
  const intelligenceData = getCapabilityData(result)
  useEffect(() => { setMode('summary') }, [key])
  useEffect(() => {
    document.body.classList.toggle('task-drawer-active', Boolean(task))
    return () => document.body.classList.remove('task-drawer-active')
  }, [task])
  return <>
    <div className={`drawer-scrim ${task ? 'visible' : ''}`} onClick={onClose} />
    <aside className={`task-drawer ${task ? 'task-drawer-open' : ''}`} aria-hidden={!task}>
      <div className="agent-header"><div><div className="agent-kicker">TASK DETAILS</div><strong>{key}</strong></div><button className="icon-button" onClick={onClose}>×</button></div>
      {task && <div className="task-details">
        <h2>{String(displayTask?.title ?? task.title ?? '')}</h2>
        <div className="details-grid"><span>Статус</span><b>{String(displayTask?.status ?? task.status ?? '—')}</b><span>Исполнитель</span><b>{String(displayTask?.assignee ?? task.assignee ?? 'Не назначен')}</b><span>Приоритет</span><b>{String(displayTask?.priority ?? task.priority ?? '—')}</b><span>Спринт</span><b>{String(displayTask?.sprint_id ?? task.sprint_id ?? '—')}</b><span>Релиз</span><b>{String(displayTask?.release_id ?? task.release_id ?? '—')}</b></div>
        <div className={`description-box ${detailQ.loading ? 'description-loading' : ''}`}>
          {detailQ.loading
            ? <span className="inline-loading"><span className="loading-spinner" />Загружаю описание из AS21…</span>
            : String(displayTask?.description ?? task.description ?? 'Описание отсутствует')}
        </div>
        <div className="intelligence-tabs">
          <button className={mode === 'summary' ? 'active' : ''} onClick={() => setMode('summary')}>Резюме</button>
          <button className={mode === 'quality' ? 'active' : ''} onClick={() => setMode('quality')}>Качество</button>
          <button className={mode === 'missing' ? 'active' : ''} onClick={() => setMode('missing')}>Что не хватает</button>
          <button className={mode === 'history' ? 'active' : ''} onClick={() => setMode('history')}>История</button>
        </div>
        <div className={`intelligence-box ${intelligenceQ.loading ? 'intelligence-loading' : ''}`} aria-busy={intelligenceQ.loading}>
          <div className="intelligence-title"><strong>Task Intelligence</strong>{result?.skill && <span>{result.skill.id}@{result.skill.version}</span>}</div>
          {intelligenceQ.loading
            ? <div className="intelligence-loading-state"><span className="loading-spinner" /><div><strong>Обновляю данные…</strong><span>PO Agent выполняет запрос для выбранной вкладки</span></div></div>
            : intelligenceQ.error
              ? <div className="warning-box">Не удалось обновить данные для этой вкладки.</div>
              : <>
                  {result?.answer ? <RichAnswer text={result.answer} /> : <div className="muted">Нет данных для отображения.</div>}
                  {result?.warnings.length ? <div className="warning">{result.warnings.join(' · ')}</div> : null}
                  <IntelligenceStructuredData data={intelligenceData} />
                </>}
        </div>
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
  const [search, setSearch] = useSessionState('tasks.search', '')
  const [submitted, setSubmitted] = useSessionState('tasks.submitted-query', '')
  const [refreshNonce, setRefreshNonce] = useState(0)
  const hasSubmitted = Boolean(submitted.trim())
  const resultQ = useSnapshotHarness('tasks:nl:' + submitted, submitted, refreshNonce, hasSubmitted)
  const result = resultQ.result
  const data = getCapabilityData(result) as { tasks?: TaskRow[] }
  const hasTaskCollection = Array.isArray(data.tasks)
  const tasks = hasTaskCollection ? (data.tasks ?? []) : []
  const resultState = classifyResult(result, { loading: hasSubmitted && resultQ.refreshing, hasRun: hasSubmitted })
  const [localStatusFilter, setLocalStatusFilter] = useSessionState<'ALL' | LocalTask['status']>('tasks.local-status', 'ALL')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingLocalTask, setEditingLocalTask] = useState<LocalTask | null>(null)
  const [selectedTask, setSelectedTask] = useState<TaskRow | null>(null)
  const [localTasks, setLocalTasks] = useState<LocalTask[]>(() => {
    try {
      const raw = JSON.parse(localStorage.getItem('po-local-tasks') ?? '[]') as Array<Partial<LocalTask>>
      const ordered = raw
        .map((task, index) => ({
          ...task,
          __index: index,
          createdAt: String(task.createdAt ?? new Date().toISOString()),
        }))
        .sort((a, b) => a.createdAt.localeCompare(b.createdAt) || a.__index - b.__index)
      let next = Math.max(0, ...ordered.map(task => Number(task.number ?? 0)).filter(Number.isFinite))
      const assigned = new Map<number, number>()
      for (const task of ordered) {
        const originalIndex = task.__index
        const existing = Number(task.number ?? 0)
        assigned.set(originalIndex, existing > 0 ? existing : ++next)
      }
      return raw.map((task, index) => ({
        id: String(task.id ?? `LOCAL-${Date.now()}-${index}`),
        number: assigned.get(index) ?? index + 1,
        title: String(task.title ?? ''),
        description: String(task.description ?? ''),
        owner: String(task.owner ?? ''),
        priority: task.priority ?? 'MEDIUM',
        status: task.status ?? 'TODO',
        labels: Array.isArray(task.labels) ? task.labels : [],
        deadline: String(task.deadline ?? ''),
        createdAt: String(task.createdAt ?? new Date().toISOString()),
      }))
    } catch { return [] }
  })
  useEffect(() => { localStorage.setItem('po-local-tasks', JSON.stringify(localTasks)) }, [localTasks])
  const nextLocalNumber = useMemo(() => Math.max(0, ...localTasks.map(task => task.number || 0)) + 1, [localTasks])
  const visibleLocalTasks = useMemo(
    () => localStatusFilter === 'ALL' ? localTasks : localTasks.filter(task => task.status === localStatusFilter),
    [localTasks, localStatusFilter],
  )
  return <section className="page page-tasks"><PageHeader title="Задачи" subtitle="Свободный поиск по задачам и рабочему контексту через навыки PO Agent" extra={hasSubmitted ? <SnapshotRefresh updatedAt={[resultQ.updatedAt]} refreshing={resultQ.refreshing} refreshError={resultQ.refreshError} onRefresh={() => setRefreshNonce(value => value + 1)} /> : undefined} />
    <form className="panel filter-toolbar" onSubmit={e => {
      e.preventDefault()
      const next = search.trim()
      if (!next) return
      if (next === submitted) setRefreshNonce(value => value + 1)
      else setSubmitted(next)
    }}>
      <div className="filter-input-row free-search-row">
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Например: Открытые задачи Калачанова с вложениями в пространстве WMB"
          aria-label="Текстовый поиск"
        />
        <button type="submit">Найти</button>
        <button type="button" onClick={() => { setEditingLocalTask(null); setDrawerOpen(true) }}>+ Локальная задача</button>
      </div>
      <div className="search-examples">Можно писать естественным языком: «Задачи Семавина по рискам», «Задачи в работе в сентябрьском спринте по DMS», «Спринты в DMS».</div>
      <HarnessMeta result={result} />
    </form>
    {localTasks.length > 0 && <div className="panel local-panel">
      <div className="panel-title"><strong>Локальные задачи</strong><div className="local-panel-tools"><select value={localStatusFilter} onChange={e => setLocalStatusFilter(e.target.value as 'ALL' | LocalTask['status'])} aria-label="Статус локальных задач"><option value="ALL">Все статусы</option><option value="TODO">TODO</option><option value="IN_PROGRESS">IN PROGRESS</option><option value="BLOCKED">BLOCKED</option><option value="DONE">DONE</option></select><span>{visibleLocalTasks.length}/{localTasks.length}</span></div></div>
      {visibleLocalTasks.map(t => <div className="local-task-list-row" key={t.id}>
        <button type="button" className="local-task-open" onClick={() => { setEditingLocalTask(t); setDrawerOpen(true) }}>
          <span className="local-task-number">{localTaskCode(t.number)}</span>
          <span className="local-task-content">
            <strong>{t.title}</strong>
            <span className="local-task-meta">{t.owner || 'Без ответственного'} · {priorityLabel(t.priority)}{t.deadline ? ` · дедлайн ${new Date(t.deadline + 'T00:00:00').toLocaleDateString('ru-RU')}` : ' · без дедлайна'}</span>
            {t.labels.length > 0 && <span className="local-tag-row">{t.labels.map(label => <span className="local-tag" key={label}>{label}</span>)}</span>}
          </span>
        </button>
        <select
          className="status-pill"
          value={t.status}
          onChange={e => setLocalTasks(items => items.map(item => item.id === t.id ? { ...item, status: e.target.value as LocalTask['status'] } : item))}
          aria-label={`Статус ${localTaskCode(t.number)}`}
        >
          <option value="TODO">TODO</option>
          <option value="IN_PROGRESS">IN PROGRESS</option>
          <option value="BLOCKED">BLOCKED</option>
          <option value="DONE">DONE</option>
        </select>
        <button
          type="button"
          className="icon-button"
          aria-label={`Удалить локальную задачу ${localTaskCode(t.number)}`}
          onClick={() => setLocalTasks(items => items.filter(item => item.id !== t.id))}
        >×</button>
      </div>)}
    </div>}
    <div className="panel"><div className="panel-title"><strong>Результат поиска</strong><span>{stateAllowsBusinessData(resultState) && hasTaskCollection ? `${tasks.length}` : (result?.skill?.id ?? '—')}</span></div>
      {stateAllowsBusinessData(resultState)
        ? (hasTaskCollection
          ? (tasks.length
            ? <div className="task-card-grid">{tasks.map(t => <TaskCard key={String(t.key)} task={t} onOpen={setSelectedTask} />)}</div>
            : <EmptyData text="Источник подтвердил: задачи не найдены" />)
          : <div className="search-answer"><RichAnswer text={result?.answer ?? ''} /></div>)
        : (hasSubmitted ? <ResultStatePanel result={result} /> : <div className="muted search-idle">Введите запрос естественным языком и нажмите «Найти».</div>)}
    </div>
    <LocalTaskDrawer
      open={drawerOpen}
      task={editingLocalTask}
      nextNumber={nextLocalNumber}
      onClose={() => { setDrawerOpen(false); setEditingLocalTask(null) }}
      onSave={task => setLocalTasks(items => {
        const exists = items.some(item => item.id === task.id)
        return exists ? items.map(item => item.id === task.id ? task : item) : [task, ...items]
      })}
    />
    <TaskDetailsDrawer task={selectedTask} onClose={() => setSelectedTask(null)} />
  </section>
}

export function SprintPage() {
  const [sprintId, setSprintId] = useSessionState('sprint.input', 'WMB-SPRNT-1')
  const [submitted, setSubmitted] = useSessionState('sprint.submitted', 'WMB-SPRNT-1')
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
  const predictabilityRatio = typeof pd.predictability === 'number'
    ? Number(pd.predictability)
    : (typeof pd.predictability_percent === 'number' ? Number(pd.predictability_percent) / 100 : null)
  const predictabilityPercent = predictabilityRatio == null ? null : Math.round(predictabilityRatio * 1000) / 10
  const risksState = classifyResult(risks)
  const sprintUpdated = [healthQ.updatedAt, velocityQ.updatedAt, throughputQ.updatedAt, wipQ.updatedAt, predictabilityQ.updatedAt, risksQ.updatedAt]
  const sprintRefreshing = healthQ.refreshing || velocityQ.refreshing || throughputQ.refreshing || wipQ.refreshing || predictabilityQ.refreshing || risksQ.refreshing
  const sprintRefreshError = healthQ.refreshError || velocityQ.refreshError || throughputQ.refreshError || wipQ.refreshError || predictabilityQ.refreshError || risksQ.refreshError
  return <section className="page page-sprint">
    <PageHeader title="Спринты" subtitle="Velocity, throughput, WIP, predictability и очередь рисков" />
    <form className="panel entity-toolbar" onSubmit={e => { e.preventDefault(); const next = sprintId.trim().toUpperCase(); if (!next) return; if (next === submitted) setRefreshNonce(value => value + 1); else setSubmitted(next) }}><div><span>Спринт</span><input value={sprintId} onChange={e => setSprintId(e.target.value)} /></div><SnapshotStatus updatedAt={sprintUpdated} refreshing={sprintRefreshing} refreshError={sprintRefreshError} /><button type="submit">{sprintRefreshing ? 'Обновляем…' : 'Обновить'}</button></form>
    <div className="metric-grid"><MetricCard label="Scope" value={stateAllowsBusinessData(healthState) ? String(hd.total ?? '—') : '—'} /><MetricCard label="Completed" value={stateAllowsBusinessData(healthState) ? String(hd.completed ?? '—') : '—'} /><MetricCard label="Velocity" value={stateAllowsBusinessData(velocityState) ? `${String(vd.velocity ?? '—')} ${String(vd.unit ?? '')}` : '—'} /><MetricCard
      label="Predictability"
      value={stateAllowsBusinessData(predictabilityState) && predictabilityPercent != null ? `${predictabilityPercent}%` : 'н/д'}
      hint={stateAllowsBusinessData(predictabilityState)
        ? (pd.baseline_committed != null && pd.completed != null
          ? `${String(pd.completed)} / ${String(pd.baseline_committed)} committed`
          : undefined)
        : 'AS21 не отдаёт committed baseline на старт спринта'}
    /></div>
    <div className="insight-grid">
      <div className="panel insight-card"><div className="panel-title"><strong>Throughput</strong><span>{throughput?.skill?.id ?? '—'}</span></div>{stateAllowsBusinessData(throughputState) ? <><div className="insight-value">{String(td.throughput ?? '—')}</div><div className="muted">завершённых задач · unit {String(td.unit ?? 'tasks')}</div></> : <ResultStatePanel result={throughput} compact />}<HarnessMeta result={throughput} /></div>
      <div className="panel insight-card"><div className="panel-title"><strong>WIP</strong><span>{wip?.skill?.id ?? '—'}</span></div>{stateAllowsBusinessData(wipState) ? <><div className="insight-value">{String(wd.wip ?? '—')}</div><div className="muted">задач в активной работе</div></> : <ResultStatePanel result={wip} compact />}<HarnessMeta result={wip} /></div>
      <div className="panel insight-card"><div className="panel-title"><strong>Готовность</strong><span>{health?.skill?.id ?? '—'}</span></div>{stateAllowsBusinessData(healthState) ? <><div className="insight-value">{String(hd.completion_percent ?? '—')}%</div><div className="muted">{String(hd.completed ?? '—')} из {String(hd.total ?? '—')} задач</div></> : <ResultStatePanel result={health} compact />}<HarnessMeta result={health} /></div>
    </div>
    <div className="panel"><div className="panel-title"><strong>Risk Queue</strong><span>{stateAllowsBusinessData(risksState) ? String(rd.count ?? riskRows.length) : '—'}</span></div>{stateAllowsBusinessData(risksState) ? (riskRows.length ? riskRows.map(row => <div className="risk-row" key={String(row.task_key)}><div><b>{String(row.task_key)}</b><span>{String(row.title ?? '')} · {(row.reasons as string[] | undefined)?.join(', ')}</span></div><em>{String(row.rank ?? '')}</em></div>) : <div className="muted">Источник подтвердил: риски не выявлены.</div>) : <ResultStatePanel result={risks} compact />}<HarnessMeta result={risks} /></div>
  </section>
}

export function ReleasesPage() {
  const [releaseId, setReleaseId] = useSessionState('release.input', 'WMB-2024-Q3')
  const [submitted, setSubmitted] = useSessionState('release.submitted', 'WMB-2024-Q3')
  const [refreshNonce, setRefreshNonce] = useState(0)
  const scopeQ = useSnapshotHarness('release:' + submitted, `Покажи scope ${submitted}`, refreshNonce)
  const progressQ = useSnapshotHarness('release:' + submitted, `Покажи прогресс ${submitted}`, refreshNonce)
  const blockersQ = useSnapshotHarness('release:' + submitted, `Покажи блокеры ${submitted}`, refreshNonce)
  const dependenciesQ = useSnapshotHarness('release:' + submitted, `Покажи зависимости ${submitted}`, refreshNonce)
  const risksQ = useSnapshotHarness('release:' + submitted, `Покажи риски релиза ${submitted}`, refreshNonce)
  const forecastQ = useSnapshotHarness('release:' + submitted, `Покажи прогноз завершения релиза ${submitted}`, refreshNonce)
  const scope = scopeQ.result
  const progress = progressQ.result
  const blockers = blockersQ.result
  const dependencies = dependenciesQ.result
  const risks = risksQ.result
  const forecast = forecastQ.result
  const sd = getCapabilityData(scope) as { count?: number; tasks?: TaskRow[] }
  const pd = getCapabilityData(progress) as Record<string, unknown>
  const bd = getCapabilityData(blockers) as { count?: number; tasks?: TaskRow[] }
  const dd = getCapabilityData(dependencies) as { internal?: Array<Record<string, unknown>>; external?: Array<Record<string, unknown>> }
  const rd = getCapabilityData(risks) as { risk_queue?: Array<Record<string, unknown>> }
  const fd = getCapabilityData(forecast, 'release.forecast') as Record<string, unknown>
  const riskRows = rd.risk_queue ?? []
  const scopeState = classifyResult(scope)
  const progressState = classifyResult(progress)
  const blockersState = classifyResult(blockers)
  const dependenciesState = classifyResult(dependencies)
  const releaseRisksState = classifyResult(risks)
  const forecastState = classifyResult(forecast)
  const releaseUpdated = [scopeQ.updatedAt, progressQ.updatedAt, blockersQ.updatedAt, dependenciesQ.updatedAt, risksQ.updatedAt, forecastQ.updatedAt]
  const releaseRefreshing = scopeQ.refreshing || progressQ.refreshing || blockersQ.refreshing || dependenciesQ.refreshing || risksQ.refreshing || forecastQ.refreshing
  const releaseRefreshError = scopeQ.refreshError || progressQ.refreshError || blockersQ.refreshError || dependenciesQ.refreshError || risksQ.refreshError || forecastQ.refreshError
  return <section className="page page-releases">
    <PageHeader title="Релизы" subtitle="Progress, blockers, dependencies, risk queue и source-backed forecast" />
    <form className="panel entity-toolbar" onSubmit={e => { e.preventDefault(); const next = releaseId.trim().toUpperCase(); if (!next) return; if (next === submitted) setRefreshNonce(value => value + 1); else setSubmitted(next) }}><div><span>Релиз</span><input value={releaseId} onChange={e => setReleaseId(e.target.value)} /></div><SnapshotStatus updatedAt={releaseUpdated} refreshing={releaseRefreshing} refreshError={releaseRefreshError} /><button type="submit">{releaseRefreshing ? 'Обновляем…' : 'Обновить'}</button></form>
    <div className="metric-grid"><MetricCard label="Scope" value={stateAllowsBusinessData(scopeState) ? String(sd.count ?? '—') : '—'} /><MetricCard label="Completed" value={stateAllowsBusinessData(progressState) ? String(pd.completed ?? '—') : '—'} /><MetricCard label="Blocked" value={stateAllowsBusinessData(progressState) ? String(pd.blocked ?? '—') : '—'} /><MetricCard label="Готовность" value={stateAllowsBusinessData(progressState) ? `${String(pd.task_completion_percent ?? '—')}%` : '—'} hint={stateAllowsBusinessData(progressState) && pd.effort_completion_percent != null ? `effort ${String(pd.effort_completion_percent)}%` : undefined} /></div>
    <div className="content-grid"><div className="panel"><div className="panel-title"><strong>Очередь рисков релиза</strong><span>{stateAllowsBusinessData(releaseRisksState) ? riskRows.length : '—'}</span></div>{stateAllowsBusinessData(releaseRisksState) ? (riskRows.length ? riskRows.map((row, index) => { const task = (row.task ?? {}) as TaskRow; return <div className="risk-row" key={String(task.key ?? index)}><div><b>{String(task.key ?? '')}</b><span>{String(task.title ?? '')} · {((row.reasons ?? []) as string[]).join(', ')}</span></div><em>{String(row.risk_score ?? '')}</em></div> }) : <div className="muted">Источник подтвердил: риски не выявлены.</div>) : <ResultStatePanel result={risks} compact />}<HarnessMeta result={risks} /></div>
      <div className="panel"><div className="panel-title"><strong>Dependencies</strong><span>{stateAllowsBusinessData(dependenciesState) ? (dd.internal?.length ?? 0) + (dd.external?.length ?? 0) : '—'}</span></div>{stateAllowsBusinessData(dependenciesState) ? <><div className="fact-row"><span>Внутренние</span><b>{dd.internal?.length ?? 0}</b></div><div className="fact-row"><span>Внешние</span><b>{dd.external?.length ?? 0}</b></div></> : <ResultStatePanel result={dependencies} compact />}<HarnessMeta result={dependencies} /></div></div>
    <div className="panel"><div className="panel-title"><strong>Blockers</strong><span>{stateAllowsBusinessData(blockersState) ? (bd.count ?? '—') : '—'}</span></div>{stateAllowsBusinessData(blockersState) ? (bd.tasks?.length ? bd.tasks.map(task => <div className="task-row" key={String(task.key)}><div className="task-key">{String(task.key)}</div><div className="task-main"><b>{String(task.title ?? '')}</b><span>{String(task.assignee ?? 'Не назначен')}</span></div><div className="status-pill">{String(task.status ?? '')}</div></div>) : <div className="muted">Источник подтвердил: заблокированных задач нет.</div>) : <ResultStatePanel result={blockers} compact />}<HarnessMeta result={blockers} /></div>
    <div className="panel insight-card">
      <div className="panel-title"><strong>Predictability / Forecast</strong><span>{forecast?.skill?.id ?? '—'}</span></div>
      {stateAllowsBusinessData(forecastState)
        ? <>
            <div className="insight-value">
              {fd.state === 'COMPLETED'
                ? 'Завершён'
                : fd.forecast_days_remaining != null
                  ? `${String(fd.forecast_days_remaining)} дн.`
                  : String(fd.state ?? '—')}
            </div>
            <div className="muted">
              {fd.forecast_date
                ? `Прогнозная дата: ${new Date(String(fd.forecast_date)).toLocaleDateString('ru-RU')}`
                : 'Подтверждённая прогнозная дата отсутствует.'}
            </div>
          </>
        : <ResultStatePanel result={forecast} compact />}
      <HarnessMeta result={forecast} />
    </div>
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
