// All available statuses from SWTR (deduplicated by code)
// Each status is identified by its SWTR code, with label for display
// Based on workflow_statuses.yaml (AS21 schema)

export default [
  // Closed statuses
  { value: 'closed', label: 'Закрыт', aliases: ['Closed', 'closed'] },
  { value: 'CLSD_YLquKLRWNLxhnnC', label: 'Closed', aliases: [] },
  { value: 'resolved', label: 'Решен', aliases: ['Resolved', 'resolved'] },
  { value: 'RSLVD_iDxZrfBaaZfOTL', label: 'Resolved', aliases: [] },

  // Cancelled
  { value: 'CNCLLD_sGZCjxXGNmqTu', label: 'Отменена', aliases: ['Cancelled', 'cancelled'] },

  // In progress statuses
  { value: 'NPRGRS_isFIvnhYcKLkj', label: 'В работе', aliases: ['In progress', 'in_progress'] },
  { value: 'NRVW_flliPvtmmflZJSi', label: 'На ревью', aliases: ['In review', 'in_review'] },
  { value: 'Q_ymlStTGiWDtKMqTySr', label: 'Тестирование', aliases: ['QA', 'qa', 'Тестирование'] },

  // Waiting / Blocked
  { value: 'NDNF_hrFjrvcMrJRqBUB', label: 'Требуется информация', aliases: ['Need info', 'need_info'] },
  { value: 'ZRGSTR_JEPgizwlJWGww', label: 'Зарегистрирован', aliases: [] },

  // Open
  { value: 'PN_wZbmKlgyPwHIFYZAN', label: 'Открыта', aliases: ['Open', 'open'] },

  // Ready for review
  { value: 'RDFR_asxQMlBcBZiouip', label: 'Готово к ревью', aliases: ['Ready for review'] },

  // Ready for QA
  { value: 'RDFR_NiewJYNruxzlMLq', label: 'Готово к QA', aliases: ['Ready for QA'] },
]
