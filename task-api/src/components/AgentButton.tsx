import { useState } from 'react'
import { colors } from '../styles'

/** Convert hex color to rgb for use in rgba() */
function hexToRgb(hex: string): string {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result
    ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
    : '99, 102, 241' // default fallback
}

interface AgentButtonProps {
  onClick: () => void
  isExecuting?: boolean
}

export function AgentButton({ onClick, isExecuting = false }: AgentButtonProps) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={onClick}
        disabled={isExecuting}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        style={{
          width: '144px',
          height: '144px',
          backgroundColor: 'transparent',
          border: 'none',
          borderRadius: '50%',
          cursor: isExecuting ? 'not-allowed' : 'pointer',
          position: 'fixed',
          bottom: '4rem',
          right: '2rem',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: isHovered
            ? `0 0 0 6px rgba(${hexToRgb(colors.accentPrimary)}, 0.3), 0 20px 60px rgba(${hexToRgb(colors.accentPrimary)}, 0.5)`
            : `0 8px 24px rgba(${hexToRgb(colors.accentPrimary)}, 0.4)`,
          animation: isHovered ? 'pulse-glow 2s ease-in-out infinite' : 'none',
        }}
        title="Ассистент PO"
      >
        {/* GigaCode-style 3D sphere with gradient */}
        <div
          style={{
            width: '112px',
            height: '112px',
            borderRadius: '50%',
            position: 'relative',
            transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
            transform: isHovered ? 'scale(1.1)' : 'scale(1)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = `0 0 30px rgba(${hexToRgb(colors.accentPrimary)}, 0.9), 0 12px 48px rgba(${hexToRgb(colors.accentPrimary)}, 0.6)`
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = 'none'
          }}
        >
          {/* Sphere gradient background */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${colors.accentPrimary} 0%, ${colors.accentPrimaryHover} 50%, ${colors.accentLighter} 100%)`,
              boxShadow: 'inset -8px -8px 24px rgba(0, 0, 0, 0.4), inset 4px 4px 16px rgba(255, 255, 255, 0.25)',
            }}
          />
          
          {/* Highlight reflection */}
          <div 
            style={{
              position: 'absolute',
              top: '24px',
              left: '24px',
              width: '36px',
              height: '20px',
              borderRadius: '50%',
              background: 'linear-gradient(180deg, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0.15) 100%)',
            }}
          />
          
          {/* GigaCode-style icon (circle with robot face) - larger */}
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '72px',
              height: '72px',
            }}
          >
            <svg
              width="72"
              height="72"
              viewBox="0 0 48 48"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              {/* Robot head - milky white with rounded corners */}
              <rect x="8" y="10" width="32" height="28" rx="8" fill="white" stroke="rgba(255,255,255,0.3)" strokeWidth="2" />
              
              {/* Robot eyes */}
              <circle cx="18" cy="20" r="3" fill="#315fa8" />
              <circle cx="30" cy="20" r="3" fill="#315fa8" />
              
              {/* Robot mouth */}
              <path d="M18 28C18 28 20 30 24 30C28 30 30 28 30 28" stroke="#315fa8" strokeWidth="2" strokeLinecap="round" />
              
              {/* Robot antenna */}
              <line x1="24" y1="10" x2="24" y2="4" stroke="#315fa8" strokeWidth="2" />
              <circle cx="24" cy="4" r="2" fill="#315fa8" />
            </svg>
          </div>

          {/* Loading overlay */}
          {isExecuting && (
            <div
              style={{
                position: 'absolute',
                top: '0',
                left: '0',
                width: '100%',
                height: '100%',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
                background: 'rgba(0,0,0,0.2)',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  width: '40px',
                  height: '40px',
                  marginTop: '-20px',
                  marginLeft: '-20px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(255, 255, 255, 0.6)',
                  animation: 'pulse 0.5s ease-in-out infinite alternate',
                }}
              />
            </div>
          )}
        </div>

        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
          @keyframes pulse {
            0% { opacity: 0.5; transform: scale(1); }
            100% { opacity: 1; transform: scale(1.2); }
          }
          @keyframes pulse-glow {
            0%, 100% { 
              box-shadow: 0 8px 24px rgba(49, 95, 168, 0.4), 0 0 0 6px rgba(49, 95, 168, 0.15);
            }
            50% {
              box-shadow: 0 20px 60px rgba(49, 95, 168, 0.7), 0 0 40px rgba(49, 95, 168, 0.6), 0 0 0 8px rgba(49, 95, 168, 0.4);
            }
          }
        `}</style>
      </button>

      {/* Tooltip: "Ассистент PO" */}
      <div
        style={{
          position: 'absolute',
          bottom: '-32px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: '#1f2937',
          color: '#fff',
          padding: '4px 12px',
          borderRadius: '20px',
          fontSize: '0.85rem',
          fontWeight: 500,
          whiteSpace: 'nowrap',
          opacity: isHovered ? 1 : 0,
          visibility: isHovered ? 'visible' : 'hidden',
          transition: 'opacity 0.2s ease',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
        }}
      >
        Ассистент PO
      </div>
    </div>
  )
}
