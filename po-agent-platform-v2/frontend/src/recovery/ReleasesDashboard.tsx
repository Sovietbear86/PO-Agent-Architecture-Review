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
const panel: CSSProperties = { background: 'var(--surface, rgba(28,43,65,.82))', border: '1px solid rgba(143,180,216,.24)', borderRadius: 14, padding: 18, minWidth: 0 }
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
  return <div style={panel}><div style={muted}>{label}</div><div style={{ fontSize: 29, fontWeight: 750, padding: '12px 0 7px' }}>{value}</div><div style={muted}>{hint}</div></div>
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
  const complete = !!data && (data.status === 'COMPLETE' && data.has_more === false || data.total === rows.length && !data.has_more)
  const scope = complete ? 'Все версии' : `Из ${rows.length} загруженных`
  const missingDate = rows.filter(row => !row.releaseDate).length
  const shares = statuses.map(status => ({ status, count: rows.filter(r => (r.workflowStatus || 'UNKNOWN') === status).length }))
  const max = Math.max(1, ...shares.map(s => s.count))
  const upcoming = rows.filter(r => !ended.has(r.workflowStatus || '') && day(r.releaseDate) !== null && day(r.releaseDate)! >= Date.now() - 86400000)
    .sort((a, b) => (day(a.releaseDate) || 0) - (day(b.releaseDate) || 0)).slice(0, 5)

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
    <div style={{ ...panel, display: 'flex', gap: 13, alignItems: 'end', flexWrap: 'wrap', marginBottom: 15 }}>
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
    {error && <div role="alert" style={{ ...panel, marginBottom: 14, borderColor: '#c88554' }}>
      Не удалось обновить каталог: {error}. {data && stale ? 'Показан предыдущий снимок этой страницы — данные могут устареть.' : 'Нет подтверждённых данных; AS21 не подставляется вместо SberProject.'}
    </div>}
    {loading && <p aria-live="polite">Получаем данные SberProject…</p>}
    {data && <>
      <div style={{ ...grid, marginBottom: 15 }}>
        <Metric label="Всего версий" value={data.total ?? (complete ? rows.length : 'Н/Д')} hint={data.total != null ? 'Подтверждено источником' : scope} />
        <Metric label="Выпущено" value={tally(new Set(['RELEASED']))} hint={scope} />
        <Metric label="В работе / планировании" value={tally(active)} hint={scope} />
        <Metric label="Без даты выпуска" value={missingDate} hint={scope} />
      </div>
      {!complete && <p role="status" style={{ ...muted, margin: '4px 0 14px' }}>
        Загружено {rows.length} из {data.total ?? 'неизвестного количества'} версий. Статистические показатели относятся только к этой странице; полные итоги по статусам пока недоступны.
        {data.has_more && data.next_offset == null ? ' Источник не подтвердил возможность загрузить следующую страницу.' : ''}
      </p>}
      {stale && <p role="status">Данные устарели: обновление завершилось ошибкой.</p>}
      <div style={{ ...grid, marginBottom: 15 }}>
        <div style={panel}>
          <h2 style={{ marginTop: 0, fontSize: 19 }}>Распределение по статусам</h2>
          {shares.length ? shares.map(s => <div key={s.status} style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}><span>{description(s.status)}</span><b>{s.count}</b></div>
            <div style={{ height: 7, borderRadius: 8, background: 'rgba(150,170,190,.20)', marginTop: 5 }}>
              <div style={{ width: `${s.count / max * 100}%`, height: '100%', borderRadius: 8, background: '#55bce3' }} />
            </div>
          </div>) : <p style={muted}>Нет данных</p>}
          <p style={muted}>{scope.toLowerCase()}; статусы без предположений о принадлежности задач.</p>
        </div>
        <div style={panel}>
          <h2 style={{ marginTop: 0, fontSize: 19 }}>Ближайшие выпуски</h2>
          {upcoming.length ? upcoming.map(r => <button type="button" key={r.id} style={{ display: 'flex', width: '100%', justifyContent: 'space-between', padding: '11px 3px', background: 'transparent', border: 0, color: 'inherit', cursor: 'pointer', borderBottom: '1px solid rgba(150,170,190,.18)' }} onClick={() => setSelected(r.id)}>
            <span><strong>{r.versionNumber}</strong><br /><span style={muted}>{description(r.workflowStatus)}</span></span><b>{fmt(r.releaseDate)}</b>
          </button>) : <p style={muted}>В загруженных версиях нет подтверждённых будущих дат выпуска.</p>}
          <p style={muted}>Отображаются только версии с указанной датой выпуска, ещё не имеющие финального статуса.</p>
        </div>
      </div>
      <div style={{ ...panel, overflowX: 'auto', marginBottom: 15 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: 19 }}>Каталог версий <span style={muted}>({filtered.length} на странице по фильтрам)</span></h2>
          <label>Сортировка{' '}<select style={input} aria-label="Сортировка релизов" value={sortBy} onChange={e => setSortBy(e.target.value as typeof sortBy)}>
            <option value="release">Дата выпуска</option><option value="end">Дата окончания</option><option value="version">Номер версии</option>
          </select></label>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 680, fontSize: 14 }}>
          <thead><tr>{['Версия / ID', 'Статус', 'Начало', 'Окончание', 'Дата выпуска', 'Ответственный'].map(h => <th scope="col" key={h} style={{ textAlign: 'left', padding: '10px 8px', borderBottom: '1px solid rgba(150,170,190,.3)' }}>{h}</th>)}</tr></thead>
          <tbody>{filtered.map(row => <tr key={row.id} style={{ background: selected === row.id ? 'rgba(70,180,222,.14)' : 'transparent' }}>
            <td style={{ padding: '10px 8px', borderBottom: '1px solid rgba(150,170,190,.12)' }}><button type="button" onClick={() => setSelected(row.id)} aria-label={`Открыть версию ${row.versionNumber}`} style={{ color: '#73d5ff', background: 'transparent', border: 0, cursor: 'pointer', textAlign: 'left' }}><b>{row.versionNumber}</b><br /><small>{row.id}</small></button></td>
            {[description(row.workflowStatus), fmt(row.beginDate), fmt(row.endDate), fmt(row.releaseDate), row.owner || 'Нет данных'].map((v, i) => <td key={i} style={{ padding: '10px 8px', borderBottom: '1px solid rgba(150,170,190,.12)' }}>{v}</td>)}
          </tr>)}</tbody>
        </table>
        {!filtered.length && <p>Нет версий по выбранным фильтрам.</p>}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginTop: 18 }}>
          <button type="button" disabled={loading || offset === 0} onClick={() => go(Math.max(0, offset - 20))}>Назад</button>
          <span>Страница {Math.floor(offset / 20) + 1}</span>
          <button type="button" disabled={loading || !data.has_more || data.next_offset == null} onClick={() => go(data.next_offset!)}>Далее</button>
          {data.has_more && data.next_offset == null && <span style={muted}>Следующая страница не подтверждена источником</span>}
        </div>
      </div>
      {chosen && <div style={{ ...panel, marginBottom: 15 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}><h2 style={{ marginTop: 0 }}>Версия {chosen.versionNumber} · {chosen.id}</h2><button type="button" onClick={() => setSelected(null)}>Закрыть</button></div>
        <div style={grid}>
          {[['Статус', description(chosen.workflowStatus)], ['Начало', fmt(chosen.beginDate)], ['Окончание', fmt(chosen.endDate)], ['Выпуск', fmt(chosen.releaseDate)], ['Ответственный', chosen.owner || 'Нет данных'], ['Менеджер', chosen.manager || 'Нет данных']].map(([key, val]) => <div key={key}><div style={muted}>{key}</div><strong>{val}</strong></div>)}
        </div>
        <p style={{ ...muted, marginBottom: 0 }}>Связь релизов и задач AS21/SWTR существует, но технический ключ сопоставления пока не подтверждён в API. Scope, Completed, WIP, блокировки, прогноз и процент готовности не рассчитываются до проверки состава задач.</p>
      </div>}
    </>}
  </section>
}
