import React, { useState, useEffect, useCallback } from 'react'
import { useSwarmStore } from './store/swarmStore'
import { getSessions, createSession, getBlackboard, getAgents, deleteSession } from './api'
import SwarmCanvas from './components/SwarmCanvas'
import QualityDashboard from './components/QualityDashboard'
import BlackboardPanel from './components/BlackboardPanel'
import LiveLogStream from './components/LiveLogStream'
import { Zap, Plus, Wifi, WifiOff, LayoutGrid, Activity, Trash2 } from 'lucide-react'

export default function App() {
  const {
    sessions, setSessions, activeSession, setActiveSession,
    isConnected, connectWs, disconnectWs, setAgents, setBlackboard,
  } = useSwarmStore()

  const [showModal, setShowModal] = useState(false)
  const [name, setName] = useState('')
  const [spec, setSpec] = useState('')
  const [bottomTab, setBottomTab] = useState('quality')
  const [loading, setLoading] = useState(false)

  const loadSessions = useCallback(async () => {
    try {
      const data = await getSessions()
      setSessions(data)
    } catch (err) {
      console.warn('Failed to load sessions', err)
    }
  }, [setSessions])

  useEffect(() => {
    loadSessions()
    const interval = setInterval(loadSessions, 10000)
    return () => clearInterval(interval)
  }, [loadSessions])

  const selectSession = useCallback(async (session) => {
    setActiveSession(session)
    connectWs(session.id)
    try {
      const [bb, agents] = await Promise.all([
        getBlackboard(session.id),
        getAgents(session.id),
      ])
      setBlackboard(bb)
      setAgents(agents)
    } catch (err) {
      console.warn('Failed to load session data', err)
    }
  }, [setActiveSession, connectWs, setBlackboard, setAgents])

  const handleCreate = async () => {
    if (!name.trim() || !spec.trim()) return
    setLoading(true)
    try {
      const session = await createSession(name, spec)
      setSessions([session, ...sessions])
      selectSession(session)
      setShowModal(false)
      setName('')
      setSpec('')
    } catch (err) {
      console.error('Failed to create session', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (e, id) => {
    e.stopPropagation()
    if (!window.confirm('Are you sure you want to delete this session?')) return
    try {
      await deleteSession(id)
      setSessions(prev => prev.filter(s => s.id !== id))
      if (activeSession?.id === id) {
        setActiveSession(null)
        disconnectWs()
      }
    } catch (err) {
      console.error('Failed to delete session', err)
      alert('Delete failed: ' + (err?.response?.data?.detail || err.message))
      // Force refresh the list anyway in case it was actually deleted
      loadSessions()
    }
  }

  const statusColor = (status) => {
    const map = {
      PENDING: 'var(--text-muted)', PLANNING: 'var(--accent-purple)',
      ARCHITECTING: 'var(--accent-purple)', BUILDING: 'var(--accent-blue)',
      REVIEWING: 'var(--accent-cyan)', TESTING: 'var(--accent-yellow)',
      SECURING: 'var(--accent-red)', DEPLOYING: 'var(--accent-green)',
      DONE: 'var(--accent-green)', FAILED: 'var(--accent-red)',
      CANCELLED: 'var(--text-muted)',
    }
    return map[status] || 'var(--text-muted)'
  }

  return (
    <>
      {/* ── Sidebar ──────────────────────────────────── */}
      <aside style={{
        width: 280, minWidth: 280, height: '100vh',
        background: 'var(--bg-secondary)', borderRight: '1px solid var(--border)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
      }}>
        {/* Logo */}
        <div style={{ padding: '20px 16px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 'var(--radius-md)',
              background: 'var(--gradient-purple)', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              boxShadow: 'var(--shadow-glow-purple)',
            }}>
              <Zap size={20} color="white" />
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1rem', letterSpacing: '-0.01em' }}>
                SwarmForge
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 500 }}>
                ULTIMATE
              </div>
            </div>
          </div>
        </div>

        {/* New Session Button */}
        <div style={{ padding: '12px 16px' }}>
          <button className="btn btn-primary" style={{ width: '100%' }}
            onClick={() => setShowModal(true)}>
            <Plus size={16} /> New Session
          </button>
        </div>

        {/* Session List */}
        <div style={{ flex: 1, overflow: 'auto', padding: '0 8px' }}>
          {sessions.map((s) => (
            <div key={s.id}
              onClick={() => selectSession(s)}
              style={{
                padding: '12px', marginBottom: 4,
                borderRadius: 'var(--radius-md)', cursor: 'pointer',
                background: activeSession?.id === s.id ? 'var(--bg-card)' : 'transparent',
                border: activeSession?.id === s.id ? '1px solid var(--border-hover)' : '1px solid transparent',
                transition: 'all var(--transition-fast)',
              }}>
              <div style={{
                fontWeight: 500, fontSize: '0.85rem',
                display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="status-dot"
                    style={{ background: statusColor(s.status), width: 8, height: 8, borderRadius: '50%', display: 'inline-block',
                      ...(s.status === 'BUILDING' || s.status === 'TESTING' ? { animation: 'pulse 1.5s infinite' } : {}),
                    }} />
                  {s.name}
                </div>
                <Trash2 size={14} color="var(--text-muted)" onClick={(e) => handleDelete(e, s.id)} style={{ cursor: 'pointer' }} onMouseOver={e => e.currentTarget.style.color = 'var(--accent-red)'} onMouseOut={e => e.currentTarget.style.color = 'var(--text-muted)'} />
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 4 }}>
                {s.status} · Score: {s.overall_score?.toFixed(0) || '—'}
              </div>
            </div>
          ))}
          {sessions.length === 0 && (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
              No sessions yet. Create one!
            </div>
          )}
        </div>

        {/* Connection Status */}
        <div style={{
          padding: '12px 16px', borderTop: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: 8,
          fontSize: '0.75rem', color: 'var(--text-muted)',
        }}>
          {isConnected ? <Wifi size={14} color="var(--accent-green)" /> : <WifiOff size={14} />}
          {isConnected ? 'Live Connected' : 'Disconnected'}
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────── */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Top Bar */}
        <header style={{
          height: 50, padding: '0 20px', borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'var(--bg-secondary)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Activity size={16} color="var(--accent-purple)" />
            <span style={{ fontWeight: 600 }}>
              {activeSession ? activeSession.name : 'Select a session'}
            </span>
            {activeSession && (
              <span className="badge" style={{
                background: statusColor(activeSession.status) + '22',
                color: statusColor(activeSession.status),
              }}>
                {activeSession.status}
              </span>
            )}
          </div>
        </header>

        {activeSession ? (
          <>
            {/* Canvas — top 55% */}
            <div style={{ flex: '0 0 55%', borderBottom: '1px solid var(--border)' }}>
              <SwarmCanvas />
            </div>

            {/* Bottom Panel — tabs */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div className="tabs">
                {['quality', 'blackboard', 'logs'].map((t) => (
                  <button key={t} className={`tab ${bottomTab === t ? 'active' : ''}`}
                    onClick={() => setBottomTab(t)}>
                    {t.charAt(0).toUpperCase() + t.slice(1)}
                  </button>
                ))}
              </div>
              <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
                {bottomTab === 'quality' && <QualityDashboard />}
                {bottomTab === 'blackboard' && <BlackboardPanel />}
                {bottomTab === 'logs' && <LiveLogStream />}
              </div>
            </div>
          </>
        ) : (
          <div style={{
            flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexDirection: 'column', gap: 16, color: 'var(--text-muted)',
          }}>
            <LayoutGrid size={48} strokeWidth={1} />
            <p style={{ fontSize: '1rem' }}>Select or create a session to begin</p>
          </div>
        )}
      </main>

      {/* ── New Session Modal ────────────────────────── */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="glass modal" onClick={(e) => e.stopPropagation()}>
            <h2>⚡ Launch New Swarm Session</h2>
            <label>Project Name</label>
            <input className="input" placeholder="my-awesome-app"
              value={name} onChange={(e) => setName(e.target.value)}
              style={{ marginBottom: 16 }} />
            <label>Software Specification</label>
            <textarea placeholder="Describe the software you want to build..."
              value={spec} onChange={(e) => setSpec(e.target.value)} rows={6} />
            <div className="actions">
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleCreate} disabled={loading}>
                {loading ? 'Launching...' : '🚀 Launch Pipeline'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
