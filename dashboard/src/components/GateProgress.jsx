import React from 'react'

export default function GateProgress({ name, score, threshold, passed, retries, maxRetries }) {
  const pct = Math.min(100, Math.max(0, (score / 100) * 100))
  const color = passed
    ? 'var(--accent-green)'
    : score >= threshold * 0.8
      ? 'var(--accent-yellow)'
      : 'var(--accent-red)'

  return (
    <div style={{
      background: 'var(--bg-card)', borderRadius: 'var(--radius-md)',
      padding: '14px 16px', border: '1px solid var(--border)',
      transition: 'all 0.2s',
    }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 8,
      }}>
        <span style={{ fontWeight: 600, fontSize: '0.85rem', textTransform: 'capitalize' }}>
          {name}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 600,
            color,
          }}>
            {score?.toFixed(1)} / {threshold}
          </span>
          <span className="badge" style={{
            background: passed ? 'var(--accent-green-dim)' : 'var(--accent-red-dim)',
            color: passed ? 'var(--accent-green)' : 'var(--accent-red)',
            fontSize: '0.65rem',
          }}>
            {passed ? 'PASS' : 'FAIL'}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="progress-bar" style={{ marginBottom: 8 }}>
        <div className="fill" style={{
          width: `${pct}%`,
          background: `linear-gradient(90deg, ${color}88, ${color})`,
        }} />
      </div>

      {/* Retry dots */}
      {maxRetries > 0 && (
        <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
          <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginRight: 4 }}>
            Retries:
          </span>
          {Array.from({ length: maxRetries }).map((_, i) => (
            <div key={i} style={{
              width: 6, height: 6, borderRadius: '50%',
              background: i < retries ? 'var(--accent-yellow)' : 'var(--border)',
              transition: 'background 0.3s',
            }} />
          ))}
        </div>
      )}
    </div>
  )
}
