/** Task status enum. */
export type Status = 'todo' | 'in_progress' | 'done' | 'open' | 'in_review' | 'ready_for_review' | 'ready_for_qa' | 'qa' | 'need_info' | 'resolved' | 'closed' | 'cancelled'

/** Task interface. */
export interface Task {
  id: string
  title: string
  description?: string
  assignee?: string
  deadline?: string // ISO 8601
  sourceUrl?: string
  status: Status
  sprint?: string // Sprint ID
  createdAt?: string // ISO 8601 (camelCase)
  created_at?: string // ISO 8601 (snake_case)
  updatedAt?: string // ISO 8601 (camelCase)
  updated_at?: string // ISO 8601 (snake_case)
  sourceData?: {
    workflowStatus?: string
    workflowStatusName?: string
    [key: string]: any
  }
}

/** Input for creating a new task. */
export interface CreateTaskInput {
  title: string
  description?: string
  assignee?: string
  sourceUrl?: string
}

/** Input for updating a task. */
export interface UpdateTaskInput {
  title?: string
  description?: string
  assignee?: string
  status?: Status
}
