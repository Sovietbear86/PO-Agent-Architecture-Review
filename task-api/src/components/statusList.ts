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
  { value: 'RDFR_aNQSySeLUupRZzl', label: 'Готово к ревью', aliases: ['Ready for review'] },

  // Ready for QA
  { value: 'RDFR_NiewJYNruxzlMLq', label: 'Готово к QA', aliases: ['Ready for QA'] },

  // CRPV statuses
  { value: 'backlog', label: 'Черновик', aliases: ['Backlog', 'backlog'] },
  { value: 'planning', label: 'Планирование', aliases: ['Planning', 'planning'] },
  { value: 'need_discovery', label: 'Требует анализа', aliases: ['Need discovery', 'need_discovery'] },
  { value: 'на_экспресс_оценке', label: 'На экспресс-оценке', aliases: ['На экспресс-оценке'] },
  { value: 'экспресс_оценка_получена', label: 'Экспресс-оценка получена', aliases: ['Экспресс-оценка получена'] },
  { value: 'ready_to_development', label: 'Готов к разработке', aliases: ['Ready to development', 'ready_to_development'] },
  { value: 'BKLG_dUlfEypttblkBvP', label: 'Backlog', aliases: ['Backlog', 'BKLG'] },
  { value: 'DN_mufbufuXXMHvbHPJb', label: 'В работе', aliases: ['В работе', 'DN'] },
  { value: 'DRFT_YlusjLBMlyDdMla', label: 'Черновик', aliases: ['Дraft', 'DRFT'] },
  { value: 'GTV_PthReTdXOmlkpGGG', label: 'Готово', aliases: ['Готово', 'GTV'] },
  { value: 'D_rSxCgSKxYYvjyujbJe', label: 'Неизвестный статус', aliases: ['Неизвестный статус', 'D_rSxCgSKxYYvjyujbJe'] },

  // STS statuses
  { value: 'PN_xySDTWtJOhUePFpLX', label: 'Open (STS)', aliases: ['Open (STS)'] },
  { value: 'PRBLMN_ZghEqKJlAzmUx', label: 'В работе (STS)', aliases: ['In progress (STS)'] },
  { value: 'CNCLLD_KdSyKcQZDXagZ', label: 'Отменена (STS)', aliases: ['Cancelled (STS)'] },
  { value: 'TKRT_ADBwyXrZkGomsLb', label: 'Неизвестный (STS)', aliases: ['Unknown (STS)'] },
  { value: 'NPRVLN_IWabzIZKVLakQ', label: 'На ревью (STS)', aliases: ['Review queue (STS)'] },
  { value: 'VCHRD_StSeYYuJOJETLf', label: 'Тестирование (STS)', aliases: ['Testing (STS)'] },
  { value: 'NLZPR_KeDzRVcVYfbBmA', label: 'Готово к ревью (STS)', aliases: ['Ready for review (STS)'] },
  { value: 'NPRGRS_pCjkadCKRetgB', label: 'В работе (STS)', aliases: ['In progress (STS)'] },
  { value: 'CLSD_fcbOheeIXkmKDVj', label: 'Закрыт (STS)', aliases: ['Closed (STS)'] },
  { value: 'PSD_sGDubPwIYfGTnzvQ', label: 'Ожидание (STS)', aliases: ['Waiting (STS)'] },
  { value: 'CNCLD_zpsREmvRWcXUOz', label: 'Отменена (STS)', aliases: ['Cancelled (STS)'] },
  { value: 'DLD_wQiPNntFtlPQStJG', label: 'Отложено (STS)', aliases: ['On hold (STS)'] },
  { value: 'PBLSHD_ANnEKtHCvosJu', label: 'Опубликовано (STS)', aliases: ['Published (STS)'] },
]
