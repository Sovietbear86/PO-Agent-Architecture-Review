/** Theme variables for PO Workspace - AS21 / WORKS style */
export const colors = {
  // Backgrounds
  bgPage: '#f5f7fa',
  bgSurface: '#ffffff',
  bgSidebar: '#f7f8fb',
  bgHover: '#edf2fb',
  bgSelected: '#dfe9fb',

  // Text
  textPrimary: '#20242c',
  textSecondary: '#667085',
  textMuted: '#8a94a6',

  // Borders
  borderDefault: '#d9dee8',
  borderSoft: '#e9edf3',

  // Accents
  accentPrimary: '#315fa8',
  accentPrimaryHover: '#274f8d',
  accentSoft: '#e8f0fd',
  accentLight: '#5d85c5',
  accentLighter: '#8da6d6',

  // Status colors
  statusOpen: '#4978c4',
  statusProgress: '#4e8ccf',
  statusReview: '#6f7f9d',
  statusQa: '#4d78a7',
  statusResolved: '#43a067',
  statusClosed: '#3b9360',
  statusCancelled: '#6a7c65',
  statusWarning: '#c88732',
  statusDanger: '#b84d4d',

  // Local task color
  statusLocal: '#667085',
} as const

export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  xxl: '48px',
} as const

export const radius = {
  sm: '6px',
  md: '10px',
  lg: '16px',
  full: '999px',
} as const

export const shadows = {
  card: '0 1px 3px rgba(27, 39, 61, 0.08)',
  cardHover: '0 4px 12px rgba(27, 39, 61, 0.12)',
  sidebar: '2px 0 8px rgba(27, 39, 61, 0.04)',
} as const

export const typography = {
  fontFamily: 'Inter, "Segoe UI", Roboto, Arial, sans-serif',
  h1: { fontSize: '28px', fontWeight: 600, lineHeight: '36px' },
  h2: { fontSize: '24px', fontWeight: 600, lineHeight: '32px' },
  h3: { fontSize: '20px', fontWeight: 600, lineHeight: '28px' },
  h4: { fontSize: '18px', fontWeight: 600, lineHeight: '24px' },
  body: { fontSize: '14px', fontWeight: 400, lineHeight: '20px' },
  bodySmall: { fontSize: '13px', fontWeight: 400, lineHeight: '18px' },
  bodyXSmall: { fontSize: '12px', fontWeight: 400, lineHeight: '16px' },
  button: { fontSize: '14px', fontWeight: 500, lineHeight: '20px' },
  label: { fontSize: '12px', fontWeight: 500, lineHeight: '16px' },
  caption: { fontSize: '11px', fontWeight: 400, lineHeight: '14px' },
} as const
