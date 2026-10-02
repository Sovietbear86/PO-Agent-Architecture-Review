export type StatusOption = {
  value: string
  label: string
  aliases?: string[]
}

// Generic community defaults. Product/workflow-specific statuses should be
// configured from source metadata rather than hard-coded by product space.
export const STATUS_OPTIONS: StatusOption[] = [
  { value: 'open', label: 'Open', aliases: ['OPEN', 'Открыт'] },
  { value: 'in_progress', label: 'In progress', aliases: ['IN PROGRESS', 'В работе'] },
  { value: 'need_info', label: 'Need info', aliases: ['NEED INFO', 'Нужна информация'] },
  { value: 'in_review', label: 'In review', aliases: ['IN REVIEW', 'На ревью'] },
  { value: 'qa', label: 'QA', aliases: ['Testing', 'Тестирование'] },
  { value: 'resolved', label: 'Resolved', aliases: ['RESOLVED', 'Решено'] },
  { value: 'closed', label: 'Closed', aliases: ['CLOSED', 'Закрыт'] },
  { value: 'cancelled', label: 'Cancelled', aliases: ['CANCELLED', 'Canceled', 'Отменён'] },
]

export function statusLabel(value?: string | null): string {
  const raw = String(value ?? '').trim()
  if (!raw) return '—'
  const normalized = raw.toLowerCase()
  const option = STATUS_OPTIONS.find(item =>
    item.value.toLowerCase() === normalized ||
    item.label.toLowerCase() === normalized ||
    item.aliases?.some(alias => alias.toLowerCase() === normalized)
  )
  return option?.label ?? raw
}
