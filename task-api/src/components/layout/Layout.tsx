import React, { ReactNode } from 'react'
import { colors } from '../../styles'

interface LayoutProps {
  sidebar: ReactNode
  content: ReactNode
  className?: string
}

export function Layout({ sidebar, content, className = '' }: LayoutProps) {
  return (
    <div className={`app-shell ${className}`} style={{ minHeight: '100vh' }}>
      {sidebar}
      <main style={{ 
        flex: 1, 
        marginLeft: '220px',
        paddingTop: '64px',
        paddingLeft: '24px',
        paddingRight: '24px',
        backgroundColor: colors.bgPage,
      }}>
        {content}
      </main>
    </div>
  )
}

export default Layout
