import React from 'react'
import { colors, spacing, radius } from '../../styles'

interface BrandingProps {
  className?: string
}

export function Branding({ className = '' }: BrandingProps) {
  return (
    <div className={`flex flex-col ${className}`}>
      {/* WORKS Logo - text based */}
      <div
        className="flex items-center gap-2 mb-2"
        style={{
          fontFamily: 'Inter, Arial, sans-serif',
        }}
      >
        <div style={{
          padding: '8px 16px',
          backgroundColor: '#315fa8',
          color: '#ffffff',
          borderRadius: '8px',
          fontWeight: 700,
          fontSize: '18px',
          letterSpacing: '1px',
        }}>
          PLATFORM V
        </div>
      </div>

      {/* DB Badge */}
      <div
        style={{
          padding: '4px 10px',
          backgroundColor: '#f5f7fa',
          border: '1px solid #d9dee8',
          color: '#315fa8',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: 600,
          width: 'fit-content',
          marginBottom: spacing.xs,
          transform: 'translateY(2px)',
        }}
      >
        DB Tribe
      </div>
    </div>
  )
}

export default Branding
