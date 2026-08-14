/**
 * Typed API client for PO Agent Platform dialogue runtime.
 * React components talk only to this module; they never call MCP/SWTR directly.
 */

import axios from 'axios'

const API_BASE_URL = '/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

export type QueryStatus = 'COMPLETED' | 'NEEDS_CLARIFICATION' | 'PARTIAL' | 'FAILED'

export interface EvidenceItem {
  type: string
  source: string
  entity_id?: string | null
  label: string
  value?: unknown
  freshness?: string | null
}

export interface HarnessQueryResponse {
  status: QueryStatus
  answer?: string | null
  question?: string | null
  options: string[]
  clarification_id?: string | null
  intent?: string | null
  skill?: { id: string; version: string } | null
  data?: unknown
  evidence: EvidenceItem[]
  warnings: string[]
  trace_id: string
  session_id: string
  correlation_id: string
  latency_ms: number
}

export interface HarnessQueryRequest {
  query: string
  session_id?: string
}

export interface FeedbackRequest {
  rating: 'up' | 'down'
  correction?: string
  expected_intent?: string
  expected_entity?: string
  comment?: string
}

export const agent = {
  query: async (request: HarnessQueryRequest): Promise<HarnessQueryResponse> => {
    const response = await api.post<HarnessQueryResponse>('/query', request)
    return response.data
  },
  feedback: async (traceId: string, request: FeedbackRequest) => {
    const response = await api.post(`/feedback/${traceId}`, request)
    return response.data
  },
  learnSemantic: async (request: { term: string; meaning: string; source_trace_id: string; scope?: string }) => {
    const response = await api.post('/learning/semantic', request)
    return response.data
  },
}

export const tasks = {
  getAll: (params?: { status?: string; assignee?: string; limit?: number; offset?: number }) =>
    api.get('/tasks', { params }),
  getById: (id: string) => api.get(`/tasks/${id}`),
  create: (data: { title: string; description?: string; assignee?: string }) => api.post('/tasks', data),
  update: (id: string, data: { title?: string; description?: string; assignee?: string }) => api.put(`/tasks/${id}`, data),
  updateStatus: (id: string, status: string) => api.patch(`/tasks/${id}/status`, { status }),
  delete: (id: string) => api.delete(`/tasks/${id}`),
}

export const quality = {
  getEvalResults: (params?: { limit?: number; offset?: number }) => api.get('/evaluations/results', { params }),
  runEvaluation: (config: { task_id: string; config: Record<string, unknown> }) => api.post('/evaluations/run', config),
}

export const team = {
  getMembers: () => api.get('/team/members'),
  getCapacity: () => api.get('/team/capacity'),
}

export const releases = {
  getAll: () => api.get('/releases'),
  getById: (id: string) => api.get(`/releases/${id}`),
  getTasks: (release_id: string) => api.get(`/releases/${release_id}/tasks`),
}

export const system = {
  health: () => api.get('/health'),
  getMetrics: () => api.get('/metrics'),
}
