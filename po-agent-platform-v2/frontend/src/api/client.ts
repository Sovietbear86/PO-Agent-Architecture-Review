/**
 * API Client for PO Agent Platform v2.1
 * Communicates with FastAPI backend on port 8004
 */

import axios from 'axios'

const API_BASE_URL = '/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Task endpoints
export const tasks = {
  getAll: (params?: { status?: string; assignee?: string; limit?: number; offset?: number }) =>
    api.get('/tasks', { params }),
  getById: (id: string) => api.get(`/tasks/${id}`),
  create: (data: { title: string; description?: string; assignee?: string }) =>
    api.post('/tasks', data),
  update: (id: string, data: { title?: string; description?: string; assignee?: string }) =>
    api.put(`/tasks/${id}`, data),
  updateStatus: (id: string, status: string) =>
    api.patch(`/tasks/${id}/status`, { status }),
  delete: (id: string) => api.delete(`/tasks/${id}`),
}

// Quality/Evaluation endpoints
export const quality = {
  getEvalResults: (params?: { limit?: number; offset?: number }) =>
    api.get('/evaluations/results', { params }),
  runEvaluation: (config: { task_id: string; config: Record<string, any> }) =>
    api.post('/evaluations/run', config),
}

// Team endpoints
export const team = {
  getMembers: () => api.get('/team/members'),
  getCapacity: () => api.get('/team/capacity'),
}

// Release endpoints
export const releases = {
  getAll: () => api.get('/releases'),
  getById: (id: string) => api.get(`/releases/${id}`),
  getTasks: (release_id: string) => api.get(`/releases/${release_id}/tasks`),
}

// System endpoints
export const system = {
  health: () => api.get('/health'),
  getMetrics: () => api.get('/metrics'),
}
