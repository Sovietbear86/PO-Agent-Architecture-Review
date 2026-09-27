import type { HarnessQueryResponse } from '../api/client'

export type ResultUiState =
  | 'NOT_RUN'
  | 'LOADING'
  | 'SUCCESS_WITH_DATA'
  | 'REAL_EMPTY'
  | 'NEEDS_CLARIFICATION'
  | 'SOURCE_CONDITIONAL'
  | 'SOURCE_UNAVAILABLE'
  | 'NOT_FOUND'
  | 'ERROR'


type CapabilityEnvelope = {
  capability_id?: string
  data?: unknown
}

export function getCapabilityData(
  result: HarnessQueryResponse | null | undefined,
  capabilityId?: string,
): Record<string, unknown> {
  const root = result?.data
  if (!root || typeof root !== 'object' || Array.isArray(root)) return {}

  const rootRecord = root as Record<string, unknown>
  const rows = Array.isArray(rootRecord.results) ? rootRecord.results : []
  const envelopes = rows
    .filter((item): item is CapabilityEnvelope => Boolean(item) && typeof item === 'object' && !Array.isArray(item))
    .filter(item => !capabilityId || item.capability_id === capabilityId)

  for (let index = envelopes.length - 1; index >= 0; index -= 1) {
    const data = envelopes[index].data
    if (data && typeof data === 'object' && !Array.isArray(data)) {
      return data as Record<string, unknown>
    }
  }

  // Some non-composed/legacy-compatible responses may already expose the
  // capability payload at result.data. Keep that shape supported, but never
  // mistake the V4 envelope itself for business data.
  if (!Array.isArray(rootRecord.results)) return rootRecord
  return {}
}

const COLLECTION_KEYS = new Set([
  'tasks', 'queue', 'risks', 'risk_queue', 'matches', 'candidates',
  'results', 'items', 'dependencies', 'members', 'sprints', 'releases',
])

const COUNT_KEYS = new Set([
  'count', 'match_count', 'candidate_count', 'total', 'total_tasks',
  'members_count', 'risk_count',
])

function records(value: unknown): Array<Record<string, unknown>> {
  if (!value || typeof value !== 'object') return []
  const root = value as Record<string, unknown>
  const found: Array<Record<string, unknown>> = [root]
  for (const child of Object.values(root)) {
    if (child && typeof child === 'object' && !Array.isArray(child)) {
      found.push(...records(child))
    }
  }
  return found
}

function warningText(result: HarnessQueryResponse): string {
  return [
    ...result.warnings,
    result.answer ?? '',
    result.question ?? '',
  ].join(' ').toLowerCase()
}

function hasSourceUnavailableSignal(result: HarnessQueryResponse): boolean {
  const text = warningText(result)
  return [
    'source_unavailable',
    'source unavailable',
    'source_capability_unavailable',
    'v4_capability_unavailable',
    'источник недоступ',
  ].some(token => text.includes(token))
}

function hasSourceConditionalSignal(result: HarnessQueryResponse): boolean {
  const text = warningText(result)
  return [
    'source_conditional',
    'source conditional',
    'insufficient source',
    'source-backed',
    'requires authoritative',
    'недостаточно данных источника',
  ].some(token => text.includes(token))
}

function hasNotFoundSignal(result: HarnessQueryResponse): boolean {
  const text = warningText(result)
  return [
    'not_found',
    'not found',
    'не найдена',
    'не найден',
  ].some(token => text.includes(token))
}

function isProvenEmptyCollection(data: unknown): boolean {
  for (const record of records(data)) {
    const collections = Object.entries(record).filter(([key, value]) => COLLECTION_KEYS.has(key) && Array.isArray(value))
    if (!collections.length) continue
    const anyNonEmpty = collections.some(([, value]) => (value as unknown[]).length > 0)
    if (anyNonEmpty) return false

    const explicitCounts = Object.entries(record)
      .filter(([key, value]) => COUNT_KEYS.has(key) && typeof value === 'number')
      .map(([, value]) => Number(value))

    if (explicitCounts.some(value => value === 0)) return true
  }
  return false
}

export function classifyResult(
  result: HarnessQueryResponse | null | undefined,
  options: { loading?: boolean; hasRun?: boolean } = {},
): ResultUiState {
  if (options.loading) return 'LOADING'
  if (!result) return options.hasRun === false ? 'NOT_RUN' : 'LOADING'

  if (result.status === 'NEEDS_CLARIFICATION') return 'NEEDS_CLARIFICATION'

  if (result.status === 'FAILED') {
    if (hasNotFoundSignal(result)) return 'NOT_FOUND'
    if (hasSourceUnavailableSignal(result)) return 'SOURCE_UNAVAILABLE'
    if (hasSourceConditionalSignal(result)) return 'SOURCE_CONDITIONAL'
    return 'ERROR'
  }

  if (result.status === 'PARTIAL') {
    if (hasSourceUnavailableSignal(result)) return 'SOURCE_UNAVAILABLE'
    return 'SOURCE_CONDITIONAL'
  }

  if (isProvenEmptyCollection(getCapabilityData(result))) return 'REAL_EMPTY'
  return 'SUCCESS_WITH_DATA'
}

export const RESULT_STATE_LABELS: Record<ResultUiState, string> = {
  NOT_RUN: 'Не запускалось',
  LOADING: 'Загрузка',
  SUCCESS_WITH_DATA: 'Данные получены',
  REAL_EMPTY: 'Пустой результат подтверждён источником',
  NEEDS_CLARIFICATION: 'Нужно уточнение',
  SOURCE_CONDITIONAL: 'Данных источника недостаточно',
  SOURCE_UNAVAILABLE: 'Источник недоступен',
  NOT_FOUND: 'Не найдено',
  ERROR: 'Ошибка',
}

export function stateAllowsBusinessData(state: ResultUiState): boolean {
  return state === 'SUCCESS_WITH_DATA' || state === 'REAL_EMPTY'
}

export function sourceStateMessage(state: ResultUiState): string {
  switch (state) {
    case 'NOT_RUN': return 'Запрос ещё не запускался.'
    case 'LOADING': return 'Получаем данные из источника…'
    case 'REAL_EMPTY': return 'Источник подтвердил, что подходящих данных нет.'
    case 'NEEDS_CLARIFICATION': return 'Для выполнения запроса нужно уточнение.'
    case 'SOURCE_CONDITIONAL': return 'Для расчёта недостаточно подтверждённых данных источника.'
    case 'SOURCE_UNAVAILABLE': return 'Источник временно недоступен. Нули не подставляются.'
    case 'NOT_FOUND': return 'Запрошенный объект не найден в источнике.'
    case 'ERROR': return 'Не удалось получить корректный результат.'
    case 'SUCCESS_WITH_DATA': return ''
  }
}
