import { create } from 'zustand'

export const useSwarmStore = create((set, get) => ({
  sessions: [],
  activeSession: null,
  agents: {},
  blackboard: null,
  logs: [],
  events: [],
  quality: null,
  isConnected: false,
  ws: null,

  // ── Session Actions ─────────────────────────────
  setSessions: (sessions) => set({ sessions }),

  setActiveSession: (session) => set({
    activeSession: session,
    agents: {},
    logs: [],
    events: [],
    quality: null,
    blackboard: null,
  }),

  updateSession: (updates) => set((state) => ({
    activeSession: state.activeSession
      ? { ...state.activeSession, ...updates }
      : null,
  })),

  // ── Agent Actions ───────────────────────────────
  updateAgentStatus: (agentId, data) => set((state) => ({
    agents: { ...state.agents, [agentId]: data },
  })),

  setAgents: (agents) => set({ agents }),

  // ── Blackboard ──────────────────────────────────
  setBlackboard: (bb) => set({ blackboard: bb }),

  // ── Logs ────────────────────────────────────────
  addLog: (log) => set((state) => ({
    logs: [log, ...state.logs].slice(0, 500),
  })),

  setLogs: (logs) => set({ logs }),

  // ── Quality ─────────────────────────────────────
  setQuality: (q) => set({ quality: q }),

  // ── Events ──────────────────────────────────────
  addEvent: (event) => set((state) => ({
    events: [...state.events, event].slice(-200),
  })),

  // ── WebSocket ───────────────────────────────────
  setConnected: (connected) => set({ isConnected: connected }),

  connectWs: (sessionId) => {
    const current = get().ws
    if (current) current.close()

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const ws = new WebSocket(`${protocol}//${host}/ws/swarm/${sessionId}`)

    ws.onopen = () => {
      set({ ws, isConnected: true })
    }

    ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data)
        if (event.type === 'keepalive') return
        get().handleSwarmEvent(event)
      } catch (err) {
        console.warn('WS parse error', err)
      }
    }

    ws.onclose = () => {
      set({ isConnected: false })
      setTimeout(() => {
        const active = get().activeSession
        if (active) get().connectWs(active.id)
      }, 3000)
    }

    ws.onerror = () => set({ isConnected: false })
    set({ ws })
  },

  disconnectWs: () => {
    const { ws } = get()
    if (ws) ws.close()
    set({ ws: null, isConnected: false })
  },

  // ── Event Handler ───────────────────────────────
  handleSwarmEvent: (event) => {
    const type = event.type || ''
    const store = get()

    // Log all events
    store.addEvent(event)

    // Agent status events
    if (type === 'agent.started') {
      store.updateAgentStatus(event.agent_id, {
        status: 'running',
        action: 'Starting...',
        model: event.model,
      })
      store.addLog({
        ts: event.ts,
        agent_id: event.agent_id,
        agent_type: event.agent_type,
        type: 'started',
        message: `Agent started (${event.model || ''})`,
      })
    }

    if (type === 'agent.done') {
      store.updateAgentStatus(event.agent_id, {
        status: 'done',
        action: 'Completed',
        duration_ms: event.duration_ms,
      })
      store.addLog({
        ts: event.ts,
        agent_id: event.agent_id,
        agent_type: event.agent_type,
        type: 'done',
        message: `Completed in ${event.duration_ms}ms`,
      })
    }

    if (type === 'agent.error') {
      store.updateAgentStatus(event.agent_id, {
        status: 'error',
        action: event.message?.slice(0, 100),
      })
      store.addLog({
        ts: event.ts,
        agent_id: event.agent_id,
        agent_type: event.agent_type,
        type: 'error',
        message: event.message,
      })
    }

    // Pipeline status
    if (type === 'pipeline.status') {
      store.updateSession({ status: event.status })
    }

    // Quality updates
    if (type === 'quality.updated') {
      store.setQuality({
        code_quality: event.code_quality,
        test_coverage: event.test_coverage,
        security_score: event.security_score,
        perf_score: event.perf_score,
        overall: event.overall,
      })
    }

    // Gate events
    if (type.startsWith('gate.')) {
      store.addLog({
        ts: event.ts,
        agent_id: 'system',
        agent_type: 'GATE',
        type: event.passed ? 'passed' : 'failed',
        message: `${type}: score ${event.score?.toFixed(1)} — ${event.passed ? 'PASSED ✓' : 'FAILED ✗'}`,
      })
    }

    // Pipeline step events (phase progress)
    if (type === 'pipeline.step') {
      store.addLog({
        ts: event.ts || new Date().toISOString(),
        agent_id: event.agent_id || 'pipeline',
        agent_type: event.agent_type || 'META',
        type: 'done',
        message: event.message,
      })
    }

    // Session done/failed
    if (type === 'session.done') {
      store.updateSession({ status: 'DONE', overall_score: event.overall_score })
    }
    if (type === 'session.failed') {
      store.updateSession({ status: 'FAILED' })
    }

    // Verdict
    if (type === 'verdict') {
      store.addLog({
        ts: event.ts,
        agent_id: 'judge',
        agent_type: 'META',
        type: event.verdict === 'GO' ? 'done' : 'error',
        message: `Verdict: ${event.verdict} — ${event.reason || ''}`,
      })
    }
  },
}))
