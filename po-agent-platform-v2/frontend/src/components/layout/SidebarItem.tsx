import React from 'react'
import { colors } from '../../styles'

interface SidebarItemProps {
  label: string
  active?: boolean
  disabled?: boolean
  onClick?: () => void
  icon?: React.ReactNode
}

export function SidebarItem({ label, active = false, disabled = false, onClick, icon }: SidebarItemProps) {
  return (
    <li
      className={`sidebar-nav-item ${active ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
      onClick={disabled ? undefined : onClick}
      style={{
        padding: '12px 16px',
        cursor: disabled ? 'default' : 'pointer',
        backgroundColor: active ? colors.bgSelected : 'transparent',
        color: active ? colors.accentPrimary : colors.textSecondary,
        borderRadius: '4px',
        marginBottom: '4px',
      }}
    >
      {icon && <span style={{ fontSize: '16px', marginRight: '8px' }}>{icon}</span>}
      <span style={{ fontWeight: active ? 600 : 400 }}>{label}</span>
    </li>
  )
}
