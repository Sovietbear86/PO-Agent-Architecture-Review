import { FormEvent, useEffect, useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { agent, HarnessQueryResponse } from '../api/client'

type WorkspaceContext = { openAgent(): void }
type Row = Record<string, unknown>

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
  return <div className="filter-status"><span>Skill: {result?.skill?.id ?? '—'}</span><span>Evidence: {result?.evidence.length ?? 0}</span><span>Trace: {result?.trace_id?.slice(0, 8) ?? '—'}</span></div>
}

function Metric({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</div>
}

export function QualityDashboard() {
  const { openAgent } = useOutletContext<WorkspaceContext>()
  const [taskKey, setTaskKey] = useState('WMB-102')
  const [submitted, setSubmitted] = useState('WMB-102')
  const [agingDays, setAgingDays] = useState('7')
  const [agingSubmitted, setAgingSubmitted] = useState('7')

  const quality = useHarness(`Оцени постановку ${submitted}`)
  const missing = useHarness(`Чего не хватает в задаче ${submitted}`)
  const acceptance = useHarness(`Покажи критерии приемки ${submitted}`)
  const aging = useHarness(`Покажи старые задачи ${agingSubmitted} дней`)

  const qd = (quality?.data ?? {}) as Row
  const md = (missing?.data ?? {}) as { missing_elements?: string[]; issues?: string[]; recommendations?: string[]; quality_score?: number }
  const ad = (acceptance?.data ?? {}) as { score?: number; criteria?: string[]; testable_criteria?: string[]; gaps?: string[] }
  const gd = (aging?.data ?? {}) as { threshold_days?: number; count?: number; tasks?: Row[] }

  const score = Number(qd.score ?? md.quality_score ?? 0)
  const acceptanceScore = Number(ad.score ?? 0)
  const missingCount = md.missing_elements?.length ?? 0
  const returnForRework = score < 70 || acceptanceScore < 70 || missingCount > 0
  const decisionLabel = returnForRework ? 'Вернуть на доработку' : 'Можно брать в работу'
  const decisionTone = returnForRework ? 'attention-badge' : 'green-badge'

  const reasons = useMemo(() => {
    const rows: string[] = []
    if (score < 70) rows.push(`Quality score ${score}/100`)
    if (acceptanceScore < 70) rows.push(`Acceptance ${acceptanceScore}/100`)
    if (missingCount) rows.push(`Пробелов: ${missingCount}`)
    return rows
  }, [score, acceptanceScore, missingCount])

  function submitTask(event: FormEvent) {
    event.preventDefault()
    if (taskKey.trim()) setSubmitted(taskKey.trim().toUpperCase())
  }

  function submitAging(event: FormEvent) {
    event.preventDefault()
    const parsed = Math.max(1, Number.parseInt(agingDays, 10) || 7)
    setAgingDays(String(parsed))
    setAgingSubmitted(String(parsed))
  }

  return <section className="page">
    <div className="page-heading"><div><h1>Качество</h1><p>Качество постановки, критерии приёмки, пробелы и aging без LLM-выдумок</p></div><button className="primary-button" onClick={openAgent}>Спросить PO Agent</button></div>

    <form className="panel entity-toolbar" onSubmit={submitTask}>
      <div><span>Задача</span><input value={taskKey} onChange={e => setTaskKey(e.target.value)} placeholder="WMB-102" /></div>
      <button type="submit">Проверить</button>
    </form>

    <div className="metric-grid">
      <Metric label="Quality score" value={`${score}/100`} hint={String(qd.quality_level ?? '') || undefined} />
      <Metric label="Acceptance" value={`${acceptanceScore}/100`} hint={`${ad.testable_criteria?.length ?? 0} проверяемых условий`} />
      <Metric label="Пробелы" value={missingCount} hint="missing requirements" />
      <Metric label="Решение PO" value={returnForRework ? 'REWORK' : 'READY'} hint={decisionLabel} />
    </div>

    <div className="quality-decision panel">
      <div><span className={decisionTone}>{decisionLabel}</span><strong>{submitted}</strong></div>
      <p>{reasons.length ? reasons.join(' · ') : 'Детерминированные проверки не выявили блокирующих пробелов в постановке.'}</p>
      <Meta result={quality} />
    </div>

    <div className="quality-grid">
      <div className="panel">
        <div className="panel-title"><strong>Что нужно уточнить</strong><span>{missingCount}</span></div>
        {md.missing_elements?.length ? md.missing_elements.map(item => <div className="quality-item" key={item}><b>{item}</b></div>) : <div className="muted">Критичных пробелов не найдено.</div>}
        {md.recommendations?.length ? <div className="recommendation-box">{md.recommendations.map(item => <div key={item}>→ {item}</div>)}</div> : null}
        <Meta result={missing} />
      </div>

      <div className="panel">
        <div className="panel-title"><strong>Acceptance / Testability</strong><span>{acceptanceScore}/100</span></div>
        {ad.criteria?.length ? ad.criteria.map((item, index) => <div className="quality-item" key={`${item}-${index}`}><b>{item}</b><span>{ad.testable_criteria?.includes(item) ? 'TESTABLE' : 'NEEDS CLARITY'}</span></div>) : <div className="muted">Явные критерии приёмки не найдены.</div>}
        {ad.gaps?.length ? <div className="warning-box">{ad.gaps.map(item => <div key={item}>⚠ {item}</div>)}</div> : null}
        <Meta result={acceptance} />
      </div>
    </div>

    <div className="panel aging-panel">
      <div className="panel-title"><strong>Aging queue</strong><span>{gd.count ?? 0}</span></div>
      <form className="aging-toolbar" onSubmit={submitAging}><label>Старше <input value={agingDays} onChange={e => setAgingDays(e.target.value)} inputMode="numeric" /> дней</label><button type="submit">Обновить</button></form>
      {gd.tasks?.length ? gd.tasks.map(task => <div className="task-row" key={String(task.key)}><div className="task-key">{String(task.key)}</div><div className="task-main"><b>{String(task.title ?? '')}</b><span>{String(task.assignee ?? 'Не назначен')} · {String(task.status ?? '')}</span></div><div className="attention-badge">{String(task.age_days ?? '')} дн.</div></div>) : <div className="muted">Задач старше выбранного порога нет.</div>}
      <Meta result={aging} />
    </div>
  </section>
}
