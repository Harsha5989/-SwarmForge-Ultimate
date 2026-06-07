import React from 'react'
import { RadialBarChart, RadialBar, ResponsiveContainer, Tooltip } from 'recharts'
import GateProgress from './GateProgress'
import { useSwarmStore } from '../store/swarmStore'
import { Shield, Zap, Bug, Gauge } from 'lucide-react'

export default function QualityDashboard() {
  const quality = useSwarmStore((s) => s.quality)
  const activeSession = useSwarmStore((s) => s.activeSession)

  const q = quality || {
    code_quality: 0, test_coverage: 0,
    security_score: 0, perf_score: 0, overall: 0,
  }

  const overall = q.overall || 0
  const overallColor = overall >= 85
    ? 'var(--accent-green)'
    : overall >= 60
      ? 'var(--accent-yellow)'
      : 'var(--accent-red)'

  const radialData = [{
    name: 'Overall', value: overall, fill: overallColor,
  }]

  return (
    <div style={{ display: 'flex', gap: 20, height: '100%', animation: 'fadeIn 0.3s ease' }}>
      {/* Left: Overall Score Ring */}
      <div style={{
        width: 220, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
      }}>
        <div style={{ position: 'relative', width: 180, height: 180 }}>
          <ResponsiveContainer>
            <RadialBarChart
              cx="50%" cy="50%" innerRadius="70%" outerRadius="100%"
              startAngle={90} endAngle={-270} data={radialData}
              barSize={12}
            >
              <RadialBar
                background={{ fill: 'var(--bg-surface)' }}
                dataKey="value" cornerRadius={6}
                isAnimationActive={true}
              />
            </RadialBarChart>
          </ResponsiveContainer>
          {/* Center label */}
          <div style={{
            position: 'absolute', inset: 0,
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{
              fontSize: '2.2rem', fontWeight: 800, color: overallColor,
              fontFamily: 'var(--font-mono)',
              transition: 'color 0.5s',
            }}>
              {overall.toFixed(0)}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              OVERALL
            </span>
          </div>
        </div>

        {/* Iteration badge */}
        <div style={{
          marginTop: 12, padding: '6px 16px',
          background: 'var(--bg-card)', borderRadius: 'var(--radius-full)',
          border: '1px solid var(--border)', fontSize: '0.75rem',
          color: 'var(--text-secondary)', fontWeight: 500,
        }}>
          Iteration {activeSession?.iteration || 0} / 5
        </div>
      </div>

      {/* Right: Gate Cards */}
      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <GateProgress
          name="🔨 Build Quality"
          score={q.code_quality}
          threshold={80}
          passed={q.code_quality >= 80}
          retries={0}
          maxRetries={3}
        />
        <GateProgress
          name="🧪 Test Coverage"
          score={q.test_coverage}
          threshold={90}
          passed={q.test_coverage >= 90}
          retries={0}
          maxRetries={3}
        />
        <GateProgress
          name="🛡️ Security"
          score={q.security_score}
          threshold={85}
          passed={q.security_score >= 85}
          retries={0}
          maxRetries={3}
        />
        <GateProgress
          name="⚡ Performance"
          score={q.perf_score}
          threshold={80}
          passed={q.perf_score >= 80}
          retries={0}
          maxRetries={3}
        />
      </div>
    </div>
  )
}
