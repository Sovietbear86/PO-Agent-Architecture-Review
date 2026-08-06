import { useEffect, ReactNode } from 'react'
import { colors, spacing, typography } from '../styles'

interface DrawerProps {
  isOpen: boolean
  onClose: () => void
  title: string
  children: ReactNode
  width?: string
}

export function Drawer({ isOpen, onClose, title, children, width = '480px' }: DrawerProps) {
  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    if (isOpen) {
      window.addEventListener('keydown', handleEscape)
    }
    return () => {
      window.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <>
      {/* Overlay */}
      <div 
        className="drawer-overlay"
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(32, 36, 44, 0.5)',
          zIndex: 1000,
          backdropFilter: 'blur(2px)',
        }}
      />
      
      {/* Drawer content */}
      <div 
        className="drawer-content"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: width,
          maxWidth: '100%',
          backgroundColor: '#ffffff',
          boxShadow: '-4px 0 20px rgba(27, 39, 61, 0.16)',
          zIndex: 1001,
          overflowY: 'auto',
        }}
      >
        {/* Header */}
        <div 
          style={{
            padding: spacing.lg,
            borderBottom: `1px solid ${colors.borderSoft}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h3 style={{ margin: 0, ...typography.h3, color: colors.textPrimary }}>
            {title}
          </h3>
          <button
            onClick={onClose}
            style={{
              padding: '4px 8px',
              fontSize: '20px',
              color: colors.textSecondary,
              cursor: 'pointer',
              background: 'none',
              border: 'none',
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>
        
        {/* Content */}
        <div style={{ padding: spacing.lg }}>
          {children}
        </div>
      </div>
    </>
  )
}

export default Drawer
