import React, { ReactNode } from 'react'
import { colors, spacing, shadows } from '../../styles'
import { Branding } from './Branding'

interface SidebarProps {
  children: ReactNode
  className?: string
}

export function Sidebar({ children, className = '' }: SidebarProps) {
  return (
    <aside
      className={`sidebar ${className}`}
      style={{
        width: '220px',
        backgroundColor: colors.bgSidebar,
        borderRight: `1px solid ${colors.borderSoft}`,
        flexShrink: 0,
      }}
    >
      <div className="sidebar-header" style={{ padding: '16px' }}>
        <Branding />
      </div>
      <ul className="sidebar-nav" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
        {children}
      </ul>
    </aside>
  )
}
