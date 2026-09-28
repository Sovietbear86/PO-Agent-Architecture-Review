import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { HarnessQueryResponse } from '../api/client'
import { ResultStatePanel } from '../components/ResultStatePanel'
import { classifyResult, getCapabilityData, stateAllowsBusinessData } from './resultState'
import { SnapshotRefresh, useSnapshotHarness } from './pageSnapshot'

type WorkspaceContext = { openAgent(): void }
type Row = Record<string, unknown>

function MetricCard({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong>{hint && <small>{hint}</small>}</div>
}

function HarnessMeta({ result }: { result: HarnessQueryResponse | null }) {
  return <div className="filter-status"><span>Skill: {result?.skill?.id ?? '—'}</span><span>Evidence: {result?.evidence.length ?? 0}</span><span>Trace: {result?.trace_id?.slice(0, 8) ?? '—'}</span></div>
}

export function TeamDashboard() {
  const { openAgent } = useOutletContext<WorkspaceContext>()
  const [space, setSpace] = useState('DMS')
  const [refreshNonce, setRefreshNonce] = useState(0)

  const workloadQ = useSnapshotHarness('team:' + space, `Покажи нагрузку команды ${space}`, refreshNonce)
  const wipQ = useSnapshotHarness('team:' + space, `Покажи WIP команды ${space}`, refreshNonce)
  const blockedQ = useSnapshotHarness('team:' + space, `Покажи блокировки команды ${space}`, refreshNonce)
  const utilizationQ = useSnapshotHarness('team:' + space, `Покажи фактическую утилизацию команды ${space}`, refreshNonce)
  const bottlenecksQ = useSnapshotHarness('team:' + space, `Покажи узкие места команды ${space}`, refreshNonce)
  const distributionQ = useSnapshotHarness('team:' + space, `Покажи распределение задач команды ${space}`, refreshNonce)
  const workload = workloadQ.result
  const wip = wipQ.result
  const blocked = blockedQ.result
  const capacity = utilizationQ.result
  const bottlenecks = bottlenecksQ.result
  const distribution = distributionQ.result

  const workloadData = getCapabilityData(workload) as { active_tasks?: number; workload?: Row[] }
  const wipData = getCapabilityData(wip) as { total_wip?: number; by_member?: Row[] }
  const blockedData = getCapabilityData(blocked) as { total_blocked?: number; by_member?: Row[]; tasks?: string[] }
  const capacityData = getCapabilityData(capacity) as { capacity_hours_per_member?: number; total_actual_hours?: number; members?: Row[] }
  const bottleneckData = getCapabilityData(bottlenecks) as { bottlenecks?: Row[]; thresholds?: Row }
  const distributionData = getCapabilityData(distribution) as { members?: Row[] }

  const workloadRows = workloadData.workload ?? []
  const capacityRows = capacityData.members ?? []
  const bottleneckRows = bottleneckData.bottlenecks ?? []
  const distributionRows = distributionData.members ?? []
  const workloadState = classifyResult(workload)
  const capacityState = classifyResult(capacity)



  return <section className="page page-team">
    <div className="page-heading">
      <div><h1>Команда</h1><p>Нагрузка, WIP, blocked, фактическая утилизация и распределение работы</p></div>
      <div className="page-heading-actions"><SnapshotRefresh updatedAt={[workloadQ.updatedAt, wipQ.updatedAt, blockedQ.updatedAt, utilizationQ.updatedAt, bottlenecksQ.updatedAt, distributionQ.updatedAt]} refreshing={workloadQ.refreshing || wipQ.refreshing || blockedQ.refreshing || utilizationQ.refreshing || bottlenecksQ.refreshing || distributionQ.refreshing} refreshError={workloadQ.refreshError || wipQ.refreshError || blockedQ.refreshError || utilizationQ.refreshError || bottlenecksQ.refreshError || distributionQ.refreshError} onRefresh={() => setRefreshNonce(value => value + 1)} /><button className="primary-button" onClick={openAgent}>Спросить PO Agent</button></div>
    </div>

    <div className="panel entity-toolbar">
      <div><span>Пространство</span><select value={space} onChange={e => setSpace(e.target.value)}><option value="DMS">DMS</option><option value="OLP">OLP</option><option value="WMB">WMB</option><option value="CRPV">CRPV</option><option value="STS">STS</option></select></div>
      <div className="form-note">Capacity пересчитывается автоматически. Базовая рабочая неделя: 40 ч/чел.; доступность и период нормализуются owner policy.</div>
    </div>

    <div className="metric-grid">
      <MetricCard label="Активных задач" value={String(workloadData.active_tasks ?? '—')} />
      <MetricCard label="WIP" value={String(wipData.total_wip ?? '—')} />
      <MetricCard label="Blocked" value={String(blockedData.total_blocked ?? '—')} hint="требуют внимания" />
      <MetricCard label="Рабочая неделя" value="40 ч" hint="автоматический owner policy" />
    </div>

    <div className="content-grid">
      <div className="panel">
        <div className="panel-title"><strong>Активная нагрузка</strong><span>{workloadRows.length}</span></div>
        {stateAllowsBusinessData(workloadState)
          ? (workloadRows.length ? workloadRows.map(row => <div className="team-member-row" key={String(row.member)}>
            <div className="avatar">{String(row.member ?? '?').slice(0, 1).toUpperCase()}</div>
            <div className="task-main"><b>{String(row.member)}</b><span>{String(row.active_tasks ?? 0)} активных · WIP {String(row.wip ?? 0)} · blocked {String(row.blocked ?? 0)}</span></div>
            <div className="team-load"><strong>{String(row.active_tasks ?? 0)}</strong><span>active tasks</span></div>
          </div>) : <div className="muted">Источник подтвердил отсутствие активной нагрузки.</div>)
          : <ResultStatePanel result={workload} compact />}
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
      <div className="panel-title"><strong>Capacity & utilization</strong><span>{stateAllowsBusinessData(capacityState) ? capacityRows.length : '—'}</span></div>
      {stateAllowsBusinessData(capacityState) ? (capacityRows.length ? <div className="capacity-table">
        <div className="capacity-head"><span>Исполнитель</span><span>Списания</span><span>Факт / capacity</span><span>Utilization</span><span>Состояние</span></div>
        {capacityRows.map(row => {
          const utilization = Number(row.utilization_percent ?? 0)
          const capped = Math.max(0, Math.min(utilization, 100))
          return <div className="capacity-row" key={String(row.member)}>
            <div><b>{String(row.member)}</b></div>
            <span>{String(row.worklog_count ?? '—')}</span>
            <span>{String(row.actual_hours ?? '—')} / {String(row.available_capacity_hours ?? capacityData.capacity_hours_per_member ?? '—')} ч</span>
            <div className="utilization-cell"><div className="utilization-track"><div className="utilization-fill" style={{ width: `${capped}%` }} /></div><span>{String(row.utilization_percent)}%</span></div>
            <span className={row.over_capacity ? 'warning-badge' : 'green-badge'}>{row.over_capacity ? 'OVER' : 'OK'}</span>
          </div>
        })}
      </div> : <div className="muted">Источник подтвердил отсутствие оценённых активных задач для расчёта capacity.</div>) : <ResultStatePanel result={capacity} compact />}
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

    <div className="form-note release-note">Competency match и рекомендация исполнителя SOURCE_READY: используются заявленные компетенции из team_members.yaml и bounded current-sprint нагрузка. Расширенный task-archetype анализ отложен в техдолг.</div>
  </section>
}
