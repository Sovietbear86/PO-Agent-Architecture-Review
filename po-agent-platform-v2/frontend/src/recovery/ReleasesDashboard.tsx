import { useEffect, useMemo, useState, type CSSProperties } from 'react'
import { sberprojectCatalog, type SberProjectCatalog, type SberProjectVersion } from '../api/client'

/**
 * Releases dashboard v1: real SberProject VERSION metadata only.
 * Release-task membership is synchronized to AS21/SWTR, but the verified join
 * has not been wired yet. Task KPIs must not be inferred from version metadata.
 */
const labels: Record<string, string> = {
  RELEASED: 'Выпущен',
  INSTALLATION: 'Внедрение',
  PLANNING: 'Планирование',
  REALIZATION: 'Реализация',
  INSTALLED: 'Установлен',
  END_OF_SUPPORT: 'Снят с поддержки',
  TRANSFERRED: 'Передан',
  CANCELLED: 'Отменён',
  INSTALLATION_CANCELLED: 'Внедрение отменено',
}
const ended = new Set(['RELEASED', 'END_OF_SUPPORT', 'TRANSFERRED', 'CANCELLED', 'INSTALLATION_CANCELLED'])
const active = new Set(['INSTALLATION', 'PLANNING', 'REALIZATION'])
const fmt = (v?: string | null) => {
  if (!v) return 'Нет данных'
  const iso = /^\d{4}-\d{2}-\d{2}/.exec(v)?.[0]
  if (!iso) return 'Нет данных'
  const [year, month, day] = iso.split('-')
  return `${day}.${month}.${year}`
}
const description = (value?: string) => labels[value || ''] || value || 'Не указан'
const panel: CSSProperties = { minWidth: 0 } // colors, borders and surfaces come from the shared .panel theme
const muted: CSSProperties = { opacity: .73, fontSize: 13 }
/** Trust only source-declared HTTPS deep links on the known SberProject host. */
function verifiedReleaseUrl(version: SberProjectVersion): string | null {
  const candidate = version.webUrl || version.url
  if (!candidate) return null
  try {
    const parsed = new URL(candidate)
    if (parsed.protocol !== 'https:' || parsed.hostname !== 'project.sbertech.ru' || parsed.username || parsed.password) return null
    // Plain portal landing page is not a release deep link; never pass it off as one.
    if (parsed.pathname === '/' && !parsed.search && !parsed.hash) return null
    return parsed.toString()
  } catch { return null }
}

const day = (v?: string | null): number | null => {
  const iso = v && /^\d{4}-\d{2}-\d{2}/.exec(v)?.[0]
  if (!iso) return null
  const ms = Date.parse(iso + 'T00:00:00Z')
  return Number.isFinite(ms) ? ms : null
}

function Metric({ label, value, hint }: { label: string; value: string | number; hint: string }) {
  return <div className="metric-card"><span>{label}</span><strong>{value}</strong><small>{hint}</small></div>
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
    <div className="panel entity-toolbar" style={{ ...panel, display: 'flex', gap: '14px 24px', alignItems: 'center', flexWrap: 'wrap', marginBottom: 15 }}>
      <label style={{ display: 'inline-flex', alignItems: 'center', gap: 10, flex: '0 0 auto' }}>Продукт
        <select style={{ width: 190 }} aria-label="Продукт" value={product} onChange={e => switchProduct(e.target.value as 'OLP' | 'DMS')}>
          <option value="OLP">PV OLAP Analytics</option><option value="DMS">PV DataMarts</option>
        </select>
      </label>
      <label style={{ display: 'inline-flex', alignItems: 'center', gap: 10, flex: '0 0 auto' }}>Статус
        <select style={{ width: 175 }} aria-label="Статус релиза" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="">Все статусы</option>{statuses.map(value => <option key={value} value={value}>{description(value)}</option>)}
        </select>
      </label>
      <div className="filter-input-row free-search-row" style={{ flex: '1 1 280px', maxWidth: 440, minWidth: 210 }}>
        <input aria-label="Поиск версии" placeholder="Поиск версии: номер, ID, ответственный" value={search} onChange={e => setSearch(e.target.value)}
          style={{ width: '100%', minWidth: 0, background: 'var(--input-bg, #17283a)', color: 'var(--text-primary, #ecf5ff)', border: '1px solid var(--border, rgba(142,180,211,.38))', borderRadius: 9, padding: '10px 12px', colorScheme: 'dark' }} />
      </div>
      <div style={{ marginLeft: 'auto', display: 'flex', gap: 12, alignItems: 'center', justifyContent: 'flex-end', flex: '1 0 auto' }}>
        <span className="muted" style={{ fontSize: 12 }}>{data?.as_of ? `Источник: ${new Date(data.as_of).toLocaleString('ru-RU')}` : 'SberProject'}</span>
        <button className="refresh-button" type="button" disabled={loading} onClick={() => setNonce(x => x + 1)}>{loading ? 'Обновляем…' : 'Обновить'}</button>
      </div>
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
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 310px), 1fr))", gap: 14, alignItems: "stretch", marginBottom: 15 }}>
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
        <div className="panel insight-card" style={{ ...panel, display: 'flex', flexDirection: 'column', minHeight: 290 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'start' }}>
            <h2 style={{ marginTop: 0, fontSize: 19 }}>Карточка релиза</h2>
            {chosen && <button type="button" onClick={() => setSelected(null)}>Закрыть</button>}
          </div>
          {chosen ? <>
            <strong style={{ fontSize: 19 }}>{chosen.versionNumber} · {chosen.id}</strong>
            <p style={{ ...muted, margin: '8px 0 12px' }}>{description(chosen.workflowStatus)}</p>
            {verifiedReleaseUrl(chosen) ? <a href={verifiedReleaseUrl(chosen)!} target="_blank" rel="noopener noreferrer" style={{ alignSelf: 'flex-start', marginBottom: 14 }}>Открыть релиз в SberProject ↗</a> : <p style={{ ...muted, margin: '0 0 12px' }}>Ссылка на конкретный релиз не передана SberProject. Открытие по неподтверждённому адресу отключено.</p>}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 10 }}>
              {[['Начало', fmt(chosen.beginDate)], ['Окончание', fmt(chosen.endDate)], ['Выпуск', fmt(chosen.releaseDate)], ['Ответственный', chosen.owner || 'Нет данных'], ['Менеджер', chosen.manager || 'Нет данных']].map(([key, val]) =>
                <div key={key}><div style={muted}>{key}</div><strong style={{ overflowWrap: 'anywhere' }}>{val}</strong></div>)}
            </div>
            <h3 style={{ fontSize: 15, margin: '18px 0 8px' }}>Задачи релиза</h3>
            <div aria-label="Задачи выбранного релиза" role="region" tabIndex={0} style={{ maxHeight: 220, minHeight: 90, overflowY: 'auto', overscrollBehavior: 'contain', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--border, rgba(143,180,216,.20))' }}>
              <p style={muted}>Задачи синхронизируются между SberProject и AS21/SWTR, но идентификатор связи и read-only API получения состава пока не проверены. Список задач временно недоступен — не подменяем его посторонними задачами и не показываем фиктивный ноль.</p>
            </div>
          </> : <p className="muted" style={{ flex: 1 }}>Выберите версию в каталоге или в блоке контрольных дат. Здесь появятся сведения о релизе и список синхронизированных задач AS21/SWTR.</p>}
        </div>
      </div>
      <div className="panel" style={{ ...panel, overflowX: 'auto', marginBottom: 15 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: 19 }}>Каталог версий <span style={muted}>({filtered.length} на странице по фильтрам)</span></h2>
          <label>Сортировка{' '}<select style={{ width: 175 }} aria-label="Сортировка релизов" value={sortBy} onChange={e => setSortBy(e.target.value as typeof sortBy)}>
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

    </>}
  </section>
}
