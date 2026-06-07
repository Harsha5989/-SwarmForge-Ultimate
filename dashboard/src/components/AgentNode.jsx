import React, { useMemo } from 'react'
import { Handle, Position } from '@xyflow/react'
import { useSwarmStore } from '../store/swarmStore'

const typeColors = {
  META: { bg: 'rgba(139,92,246,0.12)', border: '#8b5cf6', text: '#c4b5fd' },
  DEV: { bg: 'rgba(16,185,129,0.12)', border: '#10b981', text: '#6ee7b7' },
  QA: { bg: 'rgba(239,68,68,0.12)', border: '#ef4444', text: '#fca5a5' },
  OPS: { bg: 'rgba(59,130,246,0.12)', border: '#3b82f6', text: '#93c5fd' },
  JUDGE: { bg: 'rgba(245,158,11,0.12)', border: '#f59e0b', text: '#fcd34d' },
}

const statusStyles = {
  idle: { dot: '#5a5a7a', glow: 'none' },
  running: { dot: '#8b5cf6', glow: '0 0 12px rgba(139,92,246,0.6)' },
  done: { dot: '#10b981', glow: '0 0 8px rgba(16,185,129,0.4)' },
  error: { dot: '#ef4444', glow: '0 0 8px rgba(239,68,68,0.4)' },
}

export default function AgentNode({ data }) {
  const agents = useSwarmStore((s) => s.agents)
  const agentData = agents[data.agentId] || {}
  const status = agentData.status || 'idle'
  const action = agentData.action || ''
  const model = agentData.model || data.model || ''

  const colors = typeColors[data.type] || typeColors.DEV
  const sDot = statusStyles[status] || statusStyles.idle

  return (
    <div style={{
      background: colors.bg,
      border: `1px solid ${status === 'running' ? colors.border : 'rgba(255,255,255,0.06)'}`,
      borderRadius: 12,
      padding: '10px 14px',
      minWidth: 150,
      backdropFilter: 'blur(8px)',
      transition: 'all 0.3s ease',
      boxShadow: status === 'running'
        ? `0 0 20px ${colors.border}33`
        : '0 2px 8px rgba(0,0,0,0.3)',
    }}>
      <Handle type="target" position={Position.Top}
        style={{ background: colors.border, width: 6, height: 6, border: 'none' }} />

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: sDot.dot, boxShadow: sDot.glow,
          ...(status === 'running' ? { animation: 'pulse 1.5s infinite' } : {}),
        }} />
        <span style={{ fontWeight: 600, fontSize: '0.8rem', color: '#f0f0ff' }}>
          {data.label}
        </span>
      </div>

      {/* Type badge */}
      <div style={{
        display: 'inline-block', padding: '1px 8px', borderRadius: 99,
        fontSize: '0.6rem', fontWeight: 700, letterSpacing: '0.06em',
        background: colors.border + '22', color: colors.text,
        marginBottom: 4,
      }}>
        {data.type}
      </div>

      {/* Action text */}
      {action && (
        <div style={{
          fontSize: '0.65rem', color: 'rgba(255,255,255,0.5)',
          marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis',
          whiteSpace: 'nowrap', maxWidth: 140,
        }}>
          {action}
        </div>
      )}

      {/* Model */}
      {model && (
        <div style={{
          fontSize: '0.6rem', color: 'rgba(255,255,255,0.3)',
          marginTop: 2, fontFamily: 'var(--font-mono)',
        }}>
          {model}
        </div>
      )}

      <Handle type="source" position={Position.Bottom}
        style={{ background: colors.border, width: 6, height: 6, border: 'none' }} />
    </div>
  )
}
