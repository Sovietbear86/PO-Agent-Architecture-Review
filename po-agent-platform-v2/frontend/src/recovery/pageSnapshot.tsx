import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { agent, HarnessQueryResponse } from '../api/client'

type SnapshotRecord = {
  result: HarnessQueryResponse
  updatedAt: string
}

const PREFIX = 'po-page-snapshot:v1:'
const REFRESH_TIMEOUT_MS = 120_000

function keyFor(namespace: string, query: string): string {
  return PREFIX + namespace + ':' + query
}

function readSnapshot(key: string): SnapshotRecord | null {
  try {
    const raw = window.sessionStorage.getItem(key)
    if (!raw) return null
    const parsed = JSON.parse(raw) as SnapshotRecord
    if (!parsed?.result || !parsed?.updatedAt) return null
    return parsed
  } catch {
    return null
  }
}

function writeSnapshot(key: string, value: SnapshotRecord) {
  try { window.sessionStorage.setItem(key, JSON.stringify(value)) } catch { /* non-fatal */ }
}

export function useSessionState<T>(key: string, fallback: T) {
  const storageKey = 'po-page-ui:v1:' + key
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = window.sessionStorage.getItem(storageKey)
      return raw == null ? fallback : JSON.parse(raw) as T
    } catch {
      return fallback
    }
  })
  useEffect(() => {
    try { window.sessionStorage.setItem(storageKey, JSON.stringify(value)) } catch { /* non-fatal */ }
  }, [storageKey, value])
  return [value, setValue] as const
}

function snapshotLabel(updatedAt: Array<string | null>) {
  const dates = updatedAt.filter(Boolean).map(value => new Date(value as string).getTime()).filter(Number.isFinite)
  const latest = dates.length ? new Date(Math.max(...dates)) : null
  return latest
    ? latest.toLocaleString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })
    : '—'
}

export function useSnapshotHarness(namespace: string, query: string, refreshNonce = 0) {
  const cacheKey = useMemo(() => keyFor(namespace, query), [namespace, query])
  const initial = useMemo(() => readSnapshot(cacheKey), [cacheKey])
  const [result, setResult] = useState<HarnessQueryResponse | null>(initial?.result ?? null)
  const [updatedAt, setUpdatedAt] = useState<string | null>(initial?.updatedAt ?? null)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshError, setRefreshError] = useState(false)
  const requestId = useRef(0)

  const load = useCallback(async () => {
    const id = ++requestId.current
    setRefreshing(true)
    setRefreshError(false)
    try {
      const next = await Promise.race([
        agent.query({ query }),
        new Promise<never>((_, reject) => {
          window.setTimeout(() => reject(new Error('page refresh timeout')), REFRESH_TIMEOUT_MS)
        }),
      ])
      if (id !== requestId.current) return
      const timestamp = new Date().toISOString()
      setResult(next)
      setUpdatedAt(timestamp)
      writeSnapshot(cacheKey, { result: next, updatedAt: timestamp })
    } catch {
      if (id === requestId.current) setRefreshError(true)
    } finally {
      if (id === requestId.current) setRefreshing(false)
    }
  }, [cacheKey, query])

  useEffect(() => {
    const cached = readSnapshot(cacheKey)
    setResult(cached?.result ?? null)
    setUpdatedAt(cached?.updatedAt ?? null)
    setRefreshError(false)
    if (!cached) void load()
    return () => { requestId.current += 1 }
  }, [cacheKey, load])

  const lastRefresh = useRef(refreshNonce)
  useEffect(() => {
    if (refreshNonce === lastRefresh.current) return
    lastRefresh.current = refreshNonce
    void load()
  }, [refreshNonce, load])

  return { result, updatedAt, refreshing, refreshError }
}

export function SnapshotRefresh({
  updatedAt,
  refreshing,
  refreshError,
  onRefresh,
}: {
  updatedAt: Array<string | null>
  refreshing: boolean
  refreshError: boolean
  onRefresh(): void
}) {
  const label = snapshotLabel(updatedAt)
  return <div className="snapshot-refresh">
    <span className={refreshError ? 'snapshot-state snapshot-state-error' : 'snapshot-state'}>
      {refreshError ? `Не удалось обновить · данные на ${label}` : `Снимок · обновлено ${label}`}
    </span>
    <button type="button" onClick={onRefresh} disabled={refreshing}>{refreshing ? 'Обновляем…' : 'Обновить'}</button>
  </div>
}


export function SnapshotStatus({
  updatedAt,
  refreshing,
  refreshError,
}: {
  updatedAt: Array<string | null>
  refreshing: boolean
  refreshError: boolean
}) {
  const label = snapshotLabel(updatedAt)
  return <span className={refreshError ? 'snapshot-state snapshot-state-error' : 'snapshot-state'}>
    {refreshing ? 'Обновляем…' : refreshError ? `Не удалось обновить · данные на ${label}` : `Последнее обновление: ${label}`}
  </span>
}
