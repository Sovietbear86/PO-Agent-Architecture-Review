import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { sberprojectCatalog, type SberProjectCatalog } from '../api/client'

/**
 * Releases dashboard v1: real SberProject VERSION metadata only.
 * Release-task membership is synchronized to AS21/SWTR, but the verified join
 * has not been wired yet. Task KPIs must not be inferred from version metadata.
 */
const labels: Record<string, string> = {
  RELEASED: 'Выпущен',
  INSTALLATION: 'Внедрение',
  PLANNING: 'Планирование',
  END_OF_SUPPORT: 'Снят с поддержки',
  TRANSFERRED: 'Передан',
  CANCELLED: 'Отменён',
  INSTALLATION_CANCELLED: 'Внедрение отменено',
}
const ended = new Set(['RELEASED', 'END_OF_SUPPORT', 'TRANSFERRED', 'CANCELLED', 'INSTALLATION_CANCELLED'])
const active = new Set(['INSTALLATION', 'PLANNING'])
const fmt = (v?: string | null) => {
  if (!v) return 'Нет данных'
  const iso = /^\d{4}-\d{2}-\d{2}/.exec(v)?.[0]
  if (!iso) return 'Нет данных'
  const [year, month, day] = iso.split('-')
  return `${day}.${month}.${year}`
}
const description = (value?: string) => labels[value || ''] || value || 'Не указан'
const panel: CSSProperties = { minWidth: 0 } // colors, borders and surfaces come from the shared .panel theme
const grid: CSSProperties = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))', gap: 14 }
const input: CSSProperties = { minWidth: 0, maxWidth: '100%', padding: '9px 12px', borderRadius: 8 }
const muted: CSSProperties = { opacity: .73, fontSize: 13 }
const day = (v?: string | null): number | null => {
  const iso = v && /^\d{4}-\d{2}-\d{2}/.exec(v)?.[0]
  if (!iso) return null
  const ms = Date.parse(iso + 'T00:00:00Z')
  return Number.isFinite(ms) ? ms : null
}

function Metric({ label, value, hint }: { label: string; value: string | number; hint: string }) {
  return <div className="metric-card" style={panel}><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="muted">{hint}</div></div>
}
export function ReleasesDashboard() {
  const [product, setProduct] = useState<'OLP' | 'DMS'>('OLP')
  const [offset, setOffset] = useState(0)
  const [nonce, setNonce] = useState(0)
  const [data, setData] = useState<SberProjectCatalog | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [stale, setStale] = useState(false)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selected, setSelected] = useState<string | null>(null)
  const [sortBy, setSortBy] = useState<'version' | 'end' | 'release'>('release')

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    sberprojectCatalog.list(product, offset)
      .then(result => {
        if (!alive) return
        if (result.status === 'SOURCE_UNAVAILABLE') throw new Error(result.reason || 'sberproject_source_unavailable')
        setData(result)
        setStale(false)
      })
      .catch(err => {
        if (!alive) return
        setError(String(err instanceof Error ? err.message : 'sberproject_source_unavailable'))
        setStale(true)
      })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [product, offset, nonce])

  const rows = data?.versions || []
  const filtered = useMemo(() => {
    const q = search.trim().toLocaleLowerCase('ru')
    return rows.filter(row =>
      (!q || [row.id, row.versionNumber, row.owner, row.manager].some(value => String(value || '').toLocaleLowerCase('ru').includes(q))) &&
      (!statusFilter || row.workflowStatus === statusFilter)
    ).slice().sort((a, b) =>
      sortBy === 'version'
        ? b.versionNumber.localeCompare(a.versionNumber, undefined, { numeric: true })
        : (day(sortBy === 'release' ? b.releaseDate : b.endDate) ?? -Infinity) - (day(sortBy === 'release' ? a.releaseDate : a.endDate) ?? -Infinity)
    )
  }, [rows, search, statusFilter, sortBy])
  const chosen = rows.find(row => row.id === selected) || null
  const statuses = [...new Set(rows.map(row => row.workflowStatus || 'UNKNOWN'))].sort()
  const tally = (types: Set<string>) => rows.filter(row => types.has(row.workflowStatus || '')).length
  const complete = !!data && offset === 0 && data.has_more === false && (data.status === 'COMPLETE' || (data.total != null && data.total === rows.length))
  const scope = complete ? 'Все версии' : `Из ${rows.length} загруженных`
  const missingDate = rows.filter(row => !row.releaseDate).length
  const shares = statuses.map(status => ({ status, count: rows.filter(r => (r.workflowStatus || 'UNKNOWN') === status).length }))
  const max = Math.max(1, ...shares.map(s => s.count))
  // SberProject CLI version projection may omit releaseDate entirely.
  // endDate is a release-plan END milestone, not evidence of an actual release.
  // Only show a fallback with an explicit label; never call it a confirmed launch.
  const milestone = (r: { releaseDate?: string | null; endDate?: string | null }) => {
    if (day(r.releaseDate) !== null) return { date: r.releaseDate, label: 'Дата выпуска (SberProject)' }
    if (day(r.endDate) !== null) return { date: r.endDate, label: 'Окончание по плану, не дата выпуска' }
    return null
  }
  const nowDay = Math.floor(Date.now() / 86400000) * 86400000
  const upcoming = rows.filter(r => !ended.has(r.workflowStatus || '') && (day(milestone(r)?.date) ?? -Infinity) >= nowDay)
    .sort((a, b) => (day(milestone(a)?.date) ?? Infinity) - (day(milestone(b)?.date) ?? Infinity)).slice(0, 5)

  function switchProduct(next: 'OLP' | 'DMS') {
    if (next === product) return
    setData(null) // never present OLP as DMS or vice versa
    setStale(false)
    setProduct(next)
    setOffset(0)
    setSelected(null)
    setStatusFilter('')
    setSearch('')
  }
  function go(next: number) {
    setData(null) // never mislabel previous page as current
    setStale(false)
    setSelected(null)
    setOffset(next)
  }

  return <section className="page page-releases" style={{ width: '100%', maxWidth: 'none' }}>
    <div style={{ marginBottom: 20 }}>
      <h1 style={{ marginBottom: 5 }}>Релизы</h1>
      <p style={muted}>Аналитика версий из SberProject · задачи релизов синхронизируются с AS21/SWTR · read-only</p>
    </div>
    <div className="panel entity-toolbar" style={{ ...panel, display: 'flex', gap: 13, alignItems: 'end', flexWrap: 'wrap', marginBottom: 15 }}>
      <label>Продукт<br /><select style={input} aria-label="Продукт" value={product} onChange={e => switchProduct(e.target.value as 'OLP' | 'DMS')}>
        <option value="OLP">PV OLAP Analytics</option><option value="DMS">PV DataMarts</option>
      </select></label>
      <label>Поиск версии<br /><input style={input} aria-label="Поиск версии" placeholder="Номер, ID, ответственный" value={search} onChange={e => setSearch(e.target.value)} /></label>
      <label>Статус<br /><select style={input} aria-label="Статус релиза" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
        <option value="">Все статусы</option>{statuses.map(s => <option key={s} value={s}>{description(s)}</option>)}
      </select></label>
      <button type="button" disabled={loading} onClick={() => setNonce(x => x + 1)}>{loading ? 'Загрузка…' : 'Обновить'}</button>
      <span style={{ ...muted, marginLeft: 'auto' }}>{data?.as_of ? `Источник: ${new Date(data.as_of).toLocaleString('ru-RU')}` : 'SberProject'}</span>
    </div>
    {error && <div className="panel" role="alert" style={{ ...panel, marginBottom: 14 }}>
      Не удалось обновить каталог: {error}. {data && stale ? 'Показан предыдущий снимок этой страницы — данные могут устареть.' : 'Нет подтверждённых данных; AS21 не подставляется вместо SberProject.'}
    </div>}
    {loading && <p aria-live="polite">Получаем данные SberProject…</p>}
    {data && <>
      <div className="metric-grid" style={{ marginBottom: 15 }}>
        <Metric label="Всего версий" value={data.total ?? (complete ? rows.length : 'Н/Д')} hint={data.total != null ? 'Подтверждено источником' : scope} />
        <Metric label="Выпущено" value={tally(new Set(['RELEASED']))} hint={scope} />
        <Metric label="В работе / планировании" value={tally(active)} hint={scope} />
        <Metric label="Без даты выпуска" value={missingDate} hint={scope} />
      </div>
      {!complete && <p role="status" style={{ ...muted, margin: '4px 0 14px' }}>
        Загружено {rows.length} из {data.total ?? 'неизвестного количества'} версий. Статистические показатели относятся только к этой странице; полные итоги по статусам пока недоступны.
        {data.has_more && data.next_offset == null ? ' Переход «Далее» недоступен: CLI не передаёт подтверждённый курсор следующей страницы. Это ограничение источника, не отсутствие следующих релизов.' : ''}
      </p>}
      {stale && <p role="status">Данные устарели: обновление завершилось ошибкой.</p>}
      <div className="insight-grid" style={{ marginBottom: 15 }}>
        <div className="panel insight-card" style={panel}>
          <h2 style={{ marginTop: 0, fontSize: 19 }}>Распределение по статусам</h2>
          {shares.length ? shares.map(s => <div key={s.status} style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}><span>{description(s.status)}</span><b>{s.count}</b></div>
            <div style={{ height: 7, borderRadius: 8, background: 'rgba(150,170,190,.20)', marginTop: 5 }}>
              <div style={{ width: `${s.count / max * 100}%`, height: '100%', borderRadius: 8, background: 'var(--accent, currentColor)' }} />
            </div>
          </div>) : <p style={muted}>Нет данных</p>}
          <p style={muted}>{scope.toLowerCase()}; статусы без предположений о принадлежности задач.</p>
        </div>
        <div className="panel insight-card" style={panel}>
          <h2 style={{ marginTop: 0, fontSize: 19 }}>Ближайшие выпуски и контрольные даты</h2>
          {upcoming.length ? upcoming.map(r => <button type="button" key={r.id} style={{ display: 'flex', width: '100%', justifyContent: 'space-between', padding: '11px 3px', background: 'transparent', border: 0, color: 'inherit', cursor: 'pointer', borderBottom: '1px solid rgba(150,170,190,.18)' }} onClick={() => setSelected(r.id)}>
            <span><strong>{r.versionNumber}</strong><br /><span style={muted}>{description(r.workflowStatus)} · {milestone(r)?.label}</span></span><b>{fmt(milestone(r)?.date)}</b>
          </button>) : <p style={muted}>В загруженных версиях нет предстоящих подтверждённых дат выпуска или плановых дат окончания.</p>}
          <p style={muted}>Показываем только версии без финального статуса и с будущей датой. Если дата выпуска отсутствует, дата окончания плана помечается отдельно. Для OLP доступны только загруженные страницы.</p>
        </div>
      </div>
      <div className="panel" style={{ ...panel, overflowX: 'auto', marginBottom: 15 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: 19 }}>Каталог версий <span style={muted}>({filtered.length} на странице по фильтрам)</span></h2>
          <label>Сортировка{' '}<select style={input} aria-label="Сортировка релизов" value={sortBy} onChange={e => setSortBy(e.target.value as typeof sortBy)}>
            <option value="release">Дата выпуска</option><option value="end">Дата окончания</option><option value="version">Номер версии</option>
          </select></label>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 680, fontSize: 14 }}>
          <thead><tr>{['Версия / ID', 'Статус', 'Начало', 'Окончание', 'Дата выпуска', 'Ответственный'].map(h => <th scope="col" key={h} style={{ textAlign: 'left', padding: '10px 8px', borderBottom: '1px solid rgba(150,170,190,.3)' }}>{h}</th>)}</tr></thead>
          <tbody>{filtered.map(row => <tr key={row.id} style={{ background: selected === row.id ? 'var(--surface-hover, rgba(255,255,255,.06))' : 'transparent' }}>
            <td style={{ padding: '10px 8px', borderBottom: '1px solid rgba(150,170,190,.12)' }}><button type="button" onClick={() => setSelected(row.id)} aria-label={`Открыть версию ${row.versionNumber}`} style={{ color: 'var(--accent, inherit)', background: 'transparent', border: 0, cursor: 'pointer', textAlign: 'left' }}><b>{row.versionNumber}</b><br /><small>{row.id}</small></button></td>
            {[description(row.workflowStatus), fmt(row.beginDate), fmt(row.endDate), fmt(row.releaseDate), row.owner || 'Нет данных'].map((v, i) => <td key={i} style={{ padding: '10px 8px', borderBottom: '1px solid rgba(150,170,190,.12)' }}>{v}</td>)}
          </tr>)}</tbody>
        </table>
        {!filtered.length && <p>Нет версий по выбранным фильтрам.</p>}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginTop: 18 }}>
          <button type="button" disabled={loading || offset === 0} onClick={() => go(Math.max(0, offset - 20))}>Назад</button>
          <span>Страница {Math.floor(offset / 20) + 1} · {rows.length} записей{data.total != null ? ` из ${data.total}` : ''}</span>
          <button type="button" disabled={loading || !data.has_more || data.next_offset == null} onClick={() => go(data.next_offset!)}>Далее</button>
          {data.has_more && data.next_offset == null && <span role="status" className="muted">«Далее» отключена: источник не предоставляет безопасную пагинацию. Не подменяем следующие версии повтором первой страницы.</span>}
        </div>
      </div>
      {chosen && <div className="panel" style={{ ...panel, marginBottom: 15 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}><h2 style={{ marginTop: 0 }}>Версия {chosen.versionNumber} · {chosen.id}</h2><button type="button" onClick={() => setSelected(null)}>Закрыть</button></div>
        <div style={grid}>
          {[['Статус', description(chosen.workflowStatus)], ['Начало', fmt(chosen.beginDate)], ['Окончание', fmt(chosen.endDate)], ['Выпуск', fmt(chosen.releaseDate)], ['Ответственный', chosen.owner || 'Нет данных'], ['Менеджер', chosen.manager || 'Нет данных']].map(([key, val]) => <div key={key}><div style={muted}>{key}</div><strong>{val}</strong></div>)}
        </div>
        <p style={{ ...muted, marginBottom: 0 }}>Связь релизов и задач AS21/SWTR существует, но технический ключ сопоставления пока не подтверждён в API. Scope, Completed, WIP, блокировки, прогноз и процент готовности не рассчитываются до проверки состава задач.</p>
      </div>}
    </>}
  </section>
}
