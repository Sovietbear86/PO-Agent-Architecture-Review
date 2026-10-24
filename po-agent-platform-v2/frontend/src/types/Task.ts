export interface Task {
  id: string
  title: string
  description?: string
  status: string
  assignee?: string
  created_at?: string
  updated_at?: string
  deadline?: string
  source?: string
  sourceUrl?: string
  sourceData?: any
  space?: string
  sprint?: string
  product?: string
}

export interface Sprint {
  id: string
  name: string
  start_date: string
  end_date: string
  goal?: string
  tasks: Task[]
}

export interface Release {
  id: string
  name: string
  start_date?: string
  target_date?: string
  description?: string
  status: string
  tasks: Task[]
}

export interface TeamMember {
  login: string
  name: string
  role: string
  skills: string[]
  capacity_hours: number
}

export interface EvaluationResult {
  id: string
  task_id: string
  quality_score: number
  issues: string[]
  timestamp: string
}
