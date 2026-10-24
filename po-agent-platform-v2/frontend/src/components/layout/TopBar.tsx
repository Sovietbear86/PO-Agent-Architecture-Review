import React from 'react'
import { colors, spacing, typography } from '../../styles'
import { Branding } from './Branding'

interface TopBarProps {
  title?: string
  subtitle?: string
  rightContent?: React.ReactNode
  className?: string
}

export function TopBar({
  title = 'PO Workspace',
  subtitle = 'Пространство владельца продукта',
  rightContent,
  className = ''
}: TopBarProps) {
  return (
    <header
      className={`topbar ${className}`}
      style={{
        backgroundColor: colors.bgSurface,
        border: `1px solid ${colors.borderSoft}`,
        borderRadius: '8px',
        marginLeft: '10px',
        marginRight: '1rem',
      }}
    >
      <div className="topbar-brand" style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
        <span
          className="topbar-brand-name"
          style={typography.h4}
        >
          {title}
        </span>
        <span
          className="topbar-brand-subtitle"
          style={typography.bodyXSmall}
        >
          {subtitle}
        </span>
      </div>
      {rightContent && (
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
          {rightContent}
        </div>
      )}
    </header>
  )
}
