import { FormEvent, useEffect, useState } from 'react'
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

function MetricCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</div>
}

function HarnessMeta({ result }: { result: HarnessQueryResponse | null }) {
  return <div className="filter-status"><span>Skill: {result?.skill?.id ?? '—'}</span><span>Evidence: {result?.evidence.length ?? 0}</span><span>Trace: {result?.trace_id?.slice(0, 8) ?? '—'}</span></div>
}

export function TeamDashboard() {
  const { openAgent } = useOutletContext<WorkspaceContext>()
  const [capacityHours, setCapacityHours] = useState('40')
  const [capacityBaseline, setCapacityBaseline] = useState('40')

  const workload = useHarness('Покажи нагрузку команды')
  const wip = useHarness('Покажи WIP команды')
  const blocked = useHarness('Покажи блокировки команды')
  const capacity = useHarness(`Покажи capacity команды ${capacityBaseline} часов`)
  const bottlenecks = useHarness('Покажи узкие места команды')
  const distribution = useHarness('Покажи распределение задач команды')

  const workloadData = (workload?.data ?? {}) as { active_tasks?: number; workload?: Row[] }
  const wipData = (wip?.data ?? {}) as { total_wip?: number; by_member?: Row[] }
  const blockedData = (blocked?.data ?? {}) as { total_blocked?: number; by_member?: Row[]; tasks?: string[] }
  const capacityData = (capacity?.data ?? {}) as { capacity_hours_per_member?: number; members?: Row[] }
  const bottleneckData = (bottlenecks?.data ?? {}) as { bottlenecks?: Row[]; thresholds?: Row }
  const distributionData = (distribution?.data ?? {}) as { members?: Row[] }

  const workloadRows = workloadData.workload ?? []
  const capacityRows = capacityData.members ?? []
  const bottleneckRows = bottleneckData.bottlenecks ?? []
  const distributionRows = distributionData.members ?? []

  function updateCapacity(event: FormEvent) {
    event.preventDefault()
    const parsed = Number(capacityHours)
    if (Number.isFinite(parsed) && parsed > 0) setCapacityBaseline(String(parsed))
  }

  return <section className="page">
    <div className="page-heading">
      <div><h1>Команда</h1><p>Нагрузка, WIP, blocked, capacity и распределение работы</p></div>
      <button className="primary-button" onClick={openAgent}>Спросить PO Agent</button>
    </div>

    <form className="panel entity-toolbar" onSubmit={updateCapacity}>
      <div><span>Capacity baseline, часов на человека</span><input value={capacityHours} onChange={e => setCapacityHours(e.target.value)} inputMode="decimal" /></div>
      <button type="submit">Пересчитать</button>
    </form>

    <div className="metric-grid">
      <MetricCard label="Активных задач" value={String(workloadData.active_tasks ?? '—')} />
      <MetricCard label="WIP" value={String(wipData.total_wip ?? '—')} />
      <MetricCard label="Blocked" value={String(blockedData.total_blocked ?? '—')} hint="требуют внимания" />
      <MetricCard label="Capacity baseline" value={`${String(capacityData.capacity_hours_per_member ?? capacityBaseline)} ч`} hint={capacity?.warnings.includes('configured_capacity_baseline') ? 'configured baseline' : undefined} />
    </div>

    <div className="content-grid">
      <div className="panel">
        <div className="panel-title"><strong>Активная нагрузка</strong><span>{workloadRows.length}</span></div>
        {workloadRows.length ? workloadRows.map(row => <div className="team-member-row" key={String(row.member)}>
          <div className="avatar">{String(row.member ?? '?').slice(0, 1).toUpperCase()}</div>
          <div className="task-main"><b>{String(row.member)}</b><span>{String(row.tasks)} задач в активном контуре</span></div>
          <div className="team-load"><strong>{String(row.estimated_hours)} ч</strong><span>estimate</span></div>
        </div>) : <div className="muted">Активная нагрузка не обнаружена.</div>}
        <HarnessMeta result={workload} />
      </div>

      <div className="panel">
        <div className="panel-title"><strong>Сигналы</strong><span>{bottleneckRows.length + Number(blockedData.total_blocked ?? 0)}</span></div>
        <div className="fact-row"><span>Blocked tasks</span><b>{String(blockedData.total_blocked ?? '—')}</b></div>
        <div className="fact-row"><span>Concentration risks</span><b>{bottleneckRows.length}</b></div>
        <div className="fact-row"><span>WIP</span><b>{String(wipData.total_wip ?? '—')}</b></div>
        {blockedData.tasks?.length ? <div className="chip-row">{blockedData.tasks.map(task => <span className="risk-chip" key={task}>{task}</span>)}</div> : null}
        <HarnessMeta result={blocked} />
      </div>
    </div>

    <div className="panel team-capacity-panel">
      <div className="panel-title"><strong>Capacity & utilization</strong><span>{capacityRows.length}</span></div>
      {capacityRows.length ? <div className="capacity-table">
        <div className="capacity-head"><span>Исполнитель</span><span>Задачи</span><span>Нагрузка</span><span>Utilization</span><span>Состояние</span></div>
        {capacityRows.map(row => {
          const utilization = Number(row.utilization_percent ?? 0)
          const capped = Math.max(0, Math.min(utilization, 100))
          return <div className="capacity-row" key={String(row.member)}>
            <div><b>{String(row.member)}</b></div>
            <span>{String(row.tasks)}</span>
            <span>{String(row.estimated_hours)} / {String(row.capacity_hours)} ч</span>
            <div className="utilization-cell"><div className="utilization-track"><div className="utilization-fill" style={{ width: `${capped}%` }} /></div><span>{String(row.utilization_percent)}%</span></div>
            <span className={row.over_capacity ? 'warning-badge' : 'green-badge'}>{row.over_capacity ? 'OVER' : 'OK'}</span>
          </div>
        })}
      </div> : <div className="muted">Нет оценённых активных задач для расчёта capacity.</div>}
      <HarnessMeta result={capacity} />
    </div>

    <div className="insight-grid">
      <div className="panel insight-card">
        <div className="panel-title"><strong>WIP по людям</strong><span>{wipData.by_member?.length ?? 0}</span></div>
        {(wipData.by_member ?? []).map(row => <div className="fact-row" key={String(row.member)}><span>{String(row.member)}</span><b>{String(row.wip)}</b></div>)}
        <HarnessMeta result={wip} />
      </div>
      <div className="panel insight-card">
        <div className="panel-title"><strong>Bottlenecks</strong><span>{bottleneckRows.length}</span></div>
        {bottleneckRows.length ? bottleneckRows.map(row => <div className="bottleneck-row" key={String(row.member)}><div><b>{String(row.member)}</b><span>{String(row.active_tasks)} активных задач</span></div><em>{String(row.share_percent)}%</em></div>) : <div className="muted">Концентраций выше порога не найдено.</div>}
        <HarnessMeta result={bottlenecks} />
      </div>
      <div className="panel insight-card">
        <div className="panel-title"><strong>Распределение</strong><span>{distributionRows.length}</span></div>
        {distributionRows.map(row => <div className="distribution-row" key={String(row.member)}><b>{String(row.member)}</b><span>{Object.entries((row.status_distribution ?? {}) as Record<string, unknown>).map(([key, value]) => `${key}: ${String(value)}`).join(' · ')}</span></div>)}
        <HarnessMeta result={distribution} />
      </div>
    </div>

    <div className="form-note release-note">Competency match и рекомендация исполнителя пока не активированы: master-spec требует подключённый источник компетенций команды. UI намеренно не имитирует эти возможности по ключевым словам.</div>
  </section>
}
