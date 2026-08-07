// All available statuses from SWTR
// Each status is identified by its SWTR code, with label for display
// Based on workflow_statuses.yaml (AS21 schema)
// Statuses that are used in multiple spaces have space prefix to avoid confusion

export default [
  // Closed statuses
  { value: 'closed', label: 'Закрыт', aliases: ['Closed', 'closed'] },
  { value: 'CLSD_YLquKLRWNLxhnnC', label: 'Closed', aliases: [] },
  { value: 'resolved', label: 'Решен', aliases: ['Resolved', 'resolved'] },
  { value: 'RSLVD_iDxZrfBaaZfOTL', label: 'Resolved', aliases: [] },

  // Cancelled
  { value: 'CNCLLD_sGZCjxXGNmqTu', label: 'Cancelled', aliases: ['Cancelled', 'cancelled'] },
  { value: 'CNCLLD_KdSyKcQZDXagZ', label: 'Cancelled (STS)', aliases: ['CANCELLED'] },
  { value: 'CNCLD_zpsREmvRWcXUOz', label: 'Cancelled (STS)', aliases: ['Canceled'] },

  // In progress statuses
  { value: 'NPRGRS_isFIvnhYcKLkj', label: 'In progress', aliases: ['In progress'] },
  { value: 'NPRGRS_pCjkadCKRetgB', label: 'In progress (STS)', aliases: ['IN PROGRESS'] },
  { value: 'in_progress', label: 'В работе', aliases: ['В работе', 'in_progress'] },
  { value: 'NRVW_flliPvtmmflZJSi', label: 'In review', aliases: ['In review'] },
  { value: 'Q_ymlStTGiWDtKMqTySr', label: 'QA', aliases: ['QA', 'qa'] },

  // Waiting / Blocked
  { value: 'NDNF_hrFjrvcMrJRqBUB', label: 'Need info', aliases: ['Need info'] },
  { value: 'ZRGSTR_JEPgizwlJWGww', label: 'Зарегистрирован', aliases: [] },

  // Open
  { value: 'PN_wZbmKlgyPwHIFYZAN', label: 'Open', aliases: ['Open', 'open'] },
  { value: 'PN_xySDTWtJOhUePFpLX', label: 'Open (STS)', aliases: ['OPEN'] },
  { value: 'TKRT_ADBwyXrZkGomsLb', label: 'Открыт (STS)', aliases: ['Открыт'] },

  // Ready for review
  { value: 'RDFR_asxQMlBcBZiouip', label: 'Ready for review', aliases: ['Ready for review'] },
  { value: 'RDFR_aNQSySeLUupRZzl', label: 'Ready for UAT', aliases: ['Ready for UAT'] },
  { value: 'NLZPR_KeDzRVcVYfbBmA', label: 'Анализ проблемы', aliases: ['Анализ проблемы', 'Ready for review'] },

  // Ready for QA
  { value: 'RDFR_NiewJYNruxzlMLq', label: 'Ready for QA', aliases: ['Ready for QA'] },

  // Waiting / Paused
  { value: 'PSD_sGDubPwIYfGTnzvQ', label: 'Paused', aliases: ['Paused'] },

  // STS specific statuses
  { value: 'DLD_wQiPNntFtlPQStJG', label: 'Delayed (STS)', aliases: ['DELAYED', 'On hold'] },
  { value: 'PBLSHD_ANnEKtHCvosJu', label: 'Published (STS)', aliases: ['Published'] },
  { value: 'VCHRD_StSeYYuJOJETLf', label: 'В очереди (STS)', aliases: ['В очереди'] },
  { value: 'PRBLMN_ZghEqKJlAzmUx', label: 'Problem analysis (STS)', aliases: ['PROBLEM ANALYSIS'] },
  { value: 'NPRVLN_IWabzIZKVLakQ', label: 'Направлено по ошибке (STS)', aliases: ['Направлено по ошибке'] },
  { value: 'CLSD_fcbOheeIXkmKDVj', label: 'Closed (STS)', aliases: ['CLOSED'] },

  // CRPV statuses
  { value: 'backlog', label: 'Backlog (CRPV)', aliases: ['Backlog'] },
  { value: 'BKLG_dUlfEypttblkBvP', label: 'Бэклог (CRPV)', aliases: ['Бэклог', 'BKLG'] },
  { value: 'planning', label: 'Planning (CRPV)', aliases: ['Planning'] },
  { value: 'need_discovery', label: 'Need discovery (CRPV)', aliases: ['Need discovery'] },
  { value: 'на_экспресс_оценке', label: 'На экспресс-оценке (CRPV)', aliases: ['На экспресс-оценке'] },
  { value: 'экспресс_оценка_получена', label: 'Экспресс-оценка получена (CRPV)', aliases: ['Экспресс-оценка получена'] },
  { value: 'ready_to_development', label: 'Ready to development (CRPV)', aliases: ['Ready to development'] },
  { value: 'DN_mufbufuXXMHvbHPJb', label: 'Done (CRPV)', aliases: ['Done'] },
  { value: 'DRFT_YlusjLBMlyDdMla', label: 'Draft (CRPV)', aliases: ['Draft'] },
  { value: 'GTV_PthReTdXOmlkpGGG', label: 'Готово (CRPV)', aliases: ['Готово'] },
  { value: 'D_rSxCgSKxYYvjyujbJe', label: 'Идея (CRPV)', aliases: ['Идея'] },
  { value: 'T_LLShmgvPtOoNNeDfME', label: 'UAT (CRPV)', aliases: ['UAT'] },
]
