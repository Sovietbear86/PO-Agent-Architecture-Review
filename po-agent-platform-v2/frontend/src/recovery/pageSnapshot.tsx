import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { agent, HarnessQueryResponse } from '../api/client'

type SnapshotRecord = {
  result: HarnessQueryResponse
  updatedAt: string
}

const PREFIX = 'po-page-snapshot:v1:'

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
      const next = await agent.query({ query })
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
  const dates = updatedAt.filter(Boolean).map(value => new Date(value as string).getTime()).filter(Number.isFinite)
  const latest = dates.length ? new Date(Math.max(...dates)) : null
  const label = latest ? latest.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'
  return <div className="snapshot-refresh">
    <span className={refreshError ? 'snapshot-state snapshot-state-error' : 'snapshot-state'}>
      {refreshError ? `Не удалось обновить · данные на ${label}` : `Снимок · обновлено ${label}`}
    </span>
    <button type="button" onClick={onRefresh} disabled={refreshing}>{refreshing ? 'Обновляем…' : 'Обновить'}</button>
  </div>
}
