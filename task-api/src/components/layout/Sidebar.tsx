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
        backgroundColor: colors.bgSidebar,
        borderRight: `1px solid ${colors.borderSoft}`,
      }}
    >
      <div className="sidebar-header">
        <Branding />
      </div>
      <ul className="sidebar-nav">
        {children}
      </ul>
    </aside>
  )
}

export default Sidebar
