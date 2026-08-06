import axios, { AxiosInstance } from 'axios'
import { Task, CreateTaskInput, UpdateTaskInput, Status } from '../types/task'

/** Get API base URL from environment variable with fallback */
function getApiBaseUrl(): string {
  const importMeta = import.meta as unknown as { env?: { VITE_API_URL?: string } }
  return importMeta.env?.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'
}

/** Create axios instance with default config */
const apiClient: AxiosInstance = axios.create({
  baseURL: getApiBaseUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
})

/** Task API interfaces */
export interface ApiTaskResponse {
  id: string
  title: string
  description?: string | null
  assignee?: string | null
  deadline?: string | null
  source_url?: string | null
  status: string
  created_at: string
  updated_at: string
  sprint?: string | null
  source?: string | null
  source_id?: string | null
  source_data?: {
    workflow_status?: string
    workflow_status_name?: string
    sprint_id?: string | null
    [key: string]: any
  }
}

/** Convert API response to domain Task */
function mapApiResponseToTask(apiTask: ApiTaskResponse): Task {
  // Extract sprint from source_data or swtr_attributes
  let sprint = apiTask.sprint ?? apiTask.source_data?.sprint_id ?? undefined
  
  // If sprint is not in source_data.sprint_id, try to get it from swtr_attributes
  if (!sprint && apiTask.source_data?.swtr_attributes) {
    const swtrAttrs = apiTask.source_data.swtr_attributes as Array<{ code: string; value?: any }>;
    const sprintAttr = swtrAttrs.find(attr => attr.code === 'scrum_board_plugin_sprint');
    if (sprintAttr && sprintAttr.value && typeof sprintAttr.value === 'object') {
      // Sprint value is an object with code/id
      sprint = sprintAttr.value.code ?? sprintAttr.value.id ?? sprintAttr.value?.value;
    }
  }
  
  return {
    id: apiTask.id,
    title: apiTask.title,
    description: apiTask.description ?? undefined,
    assignee: apiTask.assignee ?? undefined,
    deadline: apiTask.deadline ?? undefined,
    sourceUrl: apiTask.source_url ?? undefined,
    status: apiTask.status as Status,
    createdAt: apiTask.created_at,
    updatedAt: apiTask.updated_at,
    sprint: sprint,
    sourceData: apiTask.source_data,
  }
}

/** CRUD Functions */

/** Get all tasks with optional filtering */
export async function getTasks(
  filters?: {
    status?: string
    assignee?: string
  },
  limit?: number,
  offset?: number
): Promise<Task[]> {
  const params = new URLSearchParams()
  if (filters?.status) params.append('status', filters.status)
  if (filters?.assignee) params.append('assignee', filters.assignee)
  if (limit !== undefined) params.append('limit', limit.toString())
  if (offset !== undefined) params.append('offset', offset.toString())

  const response = await apiClient.get<ApiTaskResponse[]>('/tasks', {
    params,
  })
  return response.data.map(mapApiResponseToTask)
}

/** Get task by ID */
export async function getTaskById(id: string): Promise<Task | null> {
  try {
    const response = await apiClient.get<ApiTaskResponse>(`/tasks/${id}`)
    return mapApiResponseToTask(response.data)
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null
    }
    throw error
  }
}

/** Create a new task */
export async function createTask(input: CreateTaskInput): Promise<Task> {
  const response = await apiClient.post<ApiTaskResponse>('/tasks', {
    title: input.title,
    description: input.description ?? null,
    assignee: input.assignee ?? null,
  })
  return mapApiResponseToTask(response.data)
}

/** Update an existing task */
export async function updateTask(id: string, input: UpdateTaskInput): Promise<Task | null> {
  try {
    const response = await apiClient.put<ApiTaskResponse>(`/tasks/${id}`, {
      title: input.title,
      description: input.description ?? null,
      assignee: input.assignee ?? null,
    })
    return mapApiResponseToTask(response.data)
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null
    }
    throw error
  }
}

/** Update task status */
export async function updateTaskStatus(id: string, status: Task['status']): Promise<Task | null> {
  try {
    const response = await apiClient.patch<ApiTaskResponse>(`/tasks/${id}/status`, {
      status,
    })
    return mapApiResponseToTask(response.data)
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return null
    }
    throw error
  }
}

/** Delete a task */
export async function deleteTask(id: string): Promise<boolean> {
  try {
    await apiClient.delete(`/tasks/${id}`)
    return true
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      return false
    }
    throw error
  }
}

export default apiClient
