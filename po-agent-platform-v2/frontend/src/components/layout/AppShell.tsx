import React from 'react'
import { Outlet, Link } from 'react-router-dom'
import { colors, shadows } from '../../styles'

interface AppShellProps {
  sidebar: React.ReactNode
  content: React.ReactNode
}

export const AppShell: React.FC<AppShellProps> = ({ sidebar, content }) => {
  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {sidebar}
      <div style={{
        flex: 1,
        marginLeft: '220px',
        paddingTop: '64px',
        paddingLeft: '24px',
        paddingRight: '24px',
        backgroundColor: colors.bgPage,
      }}>
        {content}
      </div>
    </div>
  )
}
