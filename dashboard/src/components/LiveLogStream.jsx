import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useSwarmStore } from '../store/swarmStore'
import { ArrowDown, Trash2, Filter } from 'lucide-react'

const typeColors = {
  started: 'var(--accent-blue)',
  done: 'var(--accent-green)',
  error: 'var(--accent-red)',
  passed: 'var(--accent-green)',
  failed: 'var(--accent-red)',
}

const agentTypeColors = {
  META: '#8b5cf6',
  DEV: '#10b981',
  QA: '#ef4444',
  OPS: '#3b82f6',
  GATE: '#f59e0b',
}

export default function LiveLogStream() {
  const logs = useSwarmStore((s) => s.logs)
  const [filter, setFilter] = useState('ALL')
  const [autoScroll, setAutoScroll] = useState(true)
  const containerRef = useRef(null)

  const filters = ['ALL', 'META', 'DEV', 'QA', 'OPS', 'GATE']

  const filteredLogs = filter === 'ALL'
    ? logs
    : logs.filter((l) => l.agent_type === filter)

  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = 0
    }
  }, [filteredLogs.length, autoScroll])

  const clearLogs = useCallback(() => {
    useSwarmStore.getState().setLogs([])
  }, [])

  const formatTime = (ts) => {
    if (!ts) return ''
    try {
      const d = new Date(ts)
      return d.toLocaleTimeString('en-US', { hour12: false })
    } catch {
      return ''
    }
  }

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      animation: 'fadeIn 0.3s ease',
    }}>
      {/* Toolbar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 10, flexWrap: 'wrap', gap: 8,
      }}>
        {/* Filter buttons */}
        <div style={{ display: 'flex', gap: 4 }}>
          {filters.map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              style={{
                padding: '4px 12px', borderRadius: 'var(--radius-sm)',
                background: filter === f
                  ? (agentTypeColors[f] || 'var(--accent-purple)') + '22'
                  : 'transparent',
                color: filter === f
                  ? (agentTypeColors[f] || 'var(--accent-purple)')
                  : 'var(--text-muted)',
                border: 'none', cursor: 'pointer', fontSize: '0.75rem',
                fontWeight: 500, fontFamily: 'var(--font-sans)',
                transition: 'all var(--transition-fast)',
              }}>
              {f}
            </button>
          ))}
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-sm btn-secondary" onClick={() => setAutoScroll(!autoScroll)}
            style={{
              color: autoScroll ? 'var(--accent-green)' : 'var(--text-muted)',
              fontSize: '0.7rem',
            }}>
            <ArrowDown size={12} /> {autoScroll ? 'Auto' : 'Manual'}
          </button>
          <button className="btn btn-sm btn-secondary" onClick={clearLogs}
            style={{ fontSize: '0.7rem' }}>
            <Trash2 size={12} /> Clear
          </button>
        </div>
      </div>

      {/* Log entries */}
      <div ref={containerRef} style={{
        flex: 1, overflow: 'auto',
        background: 'var(--bg-card)', borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border)', padding: '4px 0',
        fontFamily: 'var(--font-mono)', fontSize: '0.75rem',
      }}>
        {filteredLogs.length === 0 ? (
          <div style={{
            padding: 40, textAlign: 'center', color: 'var(--text-muted)',
            fontSize: '0.8rem', fontFamily: 'var(--font-sans)',
          }}>
            Waiting for events...
          </div>
        ) : (
          filteredLogs.map((log, i) => (
            <div key={i} style={{
              padding: '5px 14px', display: 'flex', gap: 10,
              borderBottom: '1px solid rgba(255,255,255,0.02)',
              alignItems: 'flex-start',
              animation: i === 0 ? 'slideIn 0.2s ease' : 'none',
            }}>
              {/* Timestamp */}
              <span style={{ color: 'var(--text-muted)', minWidth: 65, flexShrink: 0 }}>
                {formatTime(log.ts)}
              </span>

              {/* Agent badge */}
              <span style={{
                minWidth: 80, fontSize: '0.65rem', fontWeight: 600,
                color: agentTypeColors[log.agent_type] || 'var(--text-muted)',
                flexShrink: 0,
              }}>
                [{log.agent_id || 'system'}]
              </span>

              {/* Status dot */}
              <span style={{
                width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                marginTop: 5,
                background: typeColors[log.type] || 'var(--text-muted)',
              }} />

              {/* Message */}
              <span style={{
                color: typeColors[log.type] === 'var(--accent-red)'
                  ? 'var(--accent-red)' : 'var(--text-secondary)',
                wordBreak: 'break-word', flex: 1,
              }}>
                {log.message}
              </span>
            </div>
          ))
        )}
      </div>

      {/* Footer count */}
      <div style={{
        fontSize: '0.7rem', color: 'var(--text-muted)',
        padding: '6px 0', textAlign: 'right',
      }}>
        {filteredLogs.length} entries
        {filter !== 'ALL' ? ` (filtered: ${filter})` : ''}
      </div>
    </div>
  )
}
