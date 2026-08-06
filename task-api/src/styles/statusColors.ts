import { colors } from './theme'

// Status colors using theme accent colors for blue hues
export { colors }
export const statusColors: Record<string, string> = {
  // Green - completed/closed statuses
  'done': '#27ae60',
  'Resolved': '#2ecc71',
  'resolved': '#2ecc71',
  'Closed': '#27ae60',
  'closed': '#27ae60',
  'Закрыт': '#27ae60',
  'Решен': '#2ecc71',

  // Red/Pink - cancelled/paused statuses
  'Cancelled': '#c0392b',
  'cancelled': '#c0392b',
  'Open': '#e74c3c',
  'open': '#e74c3c',
  'Зарегистрирован': '#e67e22',

  // Blue - in-progress statuses
  'in_progress': '#f39c12',
  'In progress': '#f39c12',
  'In review': '#9b59b6',
  'in_review': '#9b59b6',
  'QA': '#00bcd4',
  'qa': '#00bcd4',
  'Тестирование': '#00bcd4',
  'Need info': '#95a5a6',

  // Purple - review queue
  'Ready for review': '#8e44ad',

  // Teal - QA queue
  'Ready for QA': '#1abc9c',
}
