import React, { useMemo } from 'react'
import {
  ReactFlow, Background, Controls, MiniMap,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import AgentNode from './AgentNode'
import { useSwarmStore } from '../store/swarmStore'

const nodeTypes = { agentNode: AgentNode }

/* ── Node Layout ──────────────────────────────────────── */
const X_CENTER = 400
const Y_GAP = 100

const initialNodes = [
  // Row 1: CEO
  { id: 'ceo', type: 'agentNode', position: { x: X_CENTER - 75, y: 0 },
    data: { label: 'CEO', type: 'META', agentId: 'ceo', model: 'meta-agent' }},

  // Row 2: CPO + CTO
  { id: 'cpo', type: 'agentNode', position: { x: X_CENTER - 200, y: Y_GAP },
    data: { label: 'CPO', type: 'META', agentId: 'cpo', model: 'meta-agent' }},
  { id: 'cto', type: 'agentNode', position: { x: X_CENTER + 50, y: Y_GAP },
    data: { label: 'CTO', type: 'META', agentId: 'cto', model: 'meta-agent' }},

  // Row 3: Tech Lead
  { id: 'tech_lead', type: 'agentNode', position: { x: X_CENTER - 75, y: Y_GAP * 2 },
    data: { label: 'Tech Lead', type: 'DEV', agentId: 'tech_lead', model: 'meta-agent' }},

  // Row 4: Coders (4 parallel)
  { id: 'coder_backend', type: 'agentNode', position: { x: X_CENTER - 350, y: Y_GAP * 3 },
    data: { label: 'Backend', type: 'DEV', agentId: 'coder_backend', model: 'coder-backend' }},
  { id: 'coder_api', type: 'agentNode', position: { x: X_CENTER - 130, y: Y_GAP * 3 },
    data: { label: 'API', type: 'DEV', agentId: 'coder_api', model: 'coder-api' }},
  { id: 'coder_frontend', type: 'agentNode', position: { x: X_CENTER + 90, y: Y_GAP * 3 },
    data: { label: 'Frontend', type: 'DEV', agentId: 'coder_frontend', model: 'coder-frontend' }},
  { id: 'coder_database', type: 'agentNode', position: { x: X_CENTER + 300, y: Y_GAP * 3 },
    data: { label: 'Database', type: 'DEV', agentId: 'coder_database', model: 'coder-database' }},

  // Row 5: Reviewer
  { id: 'reviewer', type: 'agentNode', position: { x: X_CENTER - 75, y: Y_GAP * 4 },
    data: { label: 'Reviewer', type: 'DEV', agentId: 'reviewer', model: 'reviewer-agent' }},

  // Row 6: QA Lead
  { id: 'qa_lead', type: 'agentNode', position: { x: X_CENTER - 75, y: Y_GAP * 5 },
    data: { label: 'QA Lead', type: 'QA', agentId: 'qa_lead', model: 'meta-agent' }},

  // Row 7: Testers (parallel)
  { id: 'unit_tester', type: 'agentNode', position: { x: X_CENTER - 270, y: Y_GAP * 6 },
    data: { label: 'Unit Tester', type: 'QA', agentId: 'unit_tester', model: 'qa-agent' }},
  { id: 'security_auditor', type: 'agentNode', position: { x: X_CENTER - 50, y: Y_GAP * 6 },
    data: { label: 'Security', type: 'QA', agentId: 'security_auditor', model: 'security-agent' }},
  { id: 'perf_analyzer', type: 'agentNode', position: { x: X_CENTER + 180, y: Y_GAP * 6 },
    data: { label: 'Perf', type: 'QA', agentId: 'perf_analyzer', model: 'ops-agent' }},

  // Row 8: Bug Fix + Judge
  { id: 'bug_fix', type: 'agentNode', position: { x: X_CENTER - 200, y: Y_GAP * 7 },
    data: { label: 'Bug Fix', type: 'QA', agentId: 'bug_fix', model: 'qa-agent' }},
  { id: 'judge', type: 'agentNode', position: { x: X_CENTER + 60, y: Y_GAP * 7 },
    data: { label: 'Judge', type: 'JUDGE', agentId: 'judge', model: 'judge-agent' }},

  // Row 9: Ops (parallel)
  { id: 'container_agent', type: 'agentNode', position: { x: X_CENTER - 270, y: Y_GAP * 8 },
    data: { label: 'Container', type: 'OPS', agentId: 'container_agent', model: 'ops-agent' }},
  { id: 'docs_agent', type: 'agentNode', position: { x: X_CENTER - 50, y: Y_GAP * 8 },
    data: { label: 'Docs', type: 'OPS', agentId: 'docs_agent', model: 'ops-agent' }},
  { id: 'cicd_agent', type: 'agentNode', position: { x: X_CENTER + 180, y: Y_GAP * 8 },
    data: { label: 'CI/CD', type: 'OPS', agentId: 'cicd_agent', model: 'ops-agent' }},
]

const initialEdges = [
  // Planning flow
  { id: 'e-ceo-cpo', source: 'ceo', target: 'cpo', animated: false },
  { id: 'e-ceo-cto', source: 'ceo', target: 'cto', animated: false },
  { id: 'e-cpo-tl', source: 'cpo', target: 'tech_lead', animated: false },
  { id: 'e-cto-tl', source: 'cto', target: 'tech_lead', animated: false },

  // Tech Lead → Coders
  { id: 'e-tl-cb', source: 'tech_lead', target: 'coder_backend', animated: false },
  { id: 'e-tl-ca', source: 'tech_lead', target: 'coder_api', animated: false },
  { id: 'e-tl-cf', source: 'tech_lead', target: 'coder_frontend', animated: false },
  { id: 'e-tl-cd', source: 'tech_lead', target: 'coder_database', animated: false },

  // Coders → Reviewer
  { id: 'e-cb-rev', source: 'coder_backend', target: 'reviewer', animated: false },
  { id: 'e-ca-rev', source: 'coder_api', target: 'reviewer', animated: false },
  { id: 'e-cf-rev', source: 'coder_frontend', target: 'reviewer', animated: false },
  { id: 'e-cd-rev', source: 'coder_database', target: 'reviewer', animated: false },

  // Reviewer → QA Lead
  { id: 'e-rev-qa', source: 'reviewer', target: 'qa_lead', animated: false },

  // QA Lead → Testers
  { id: 'e-qa-ut', source: 'qa_lead', target: 'unit_tester', animated: false },
  { id: 'e-qa-sec', source: 'qa_lead', target: 'security_auditor', animated: false },
  { id: 'e-qa-perf', source: 'qa_lead', target: 'perf_analyzer', animated: false },

  // Testers → Bug Fix / Judge
  { id: 'e-ut-bf', source: 'unit_tester', target: 'bug_fix', animated: false },
  { id: 'e-sec-bf', source: 'security_auditor', target: 'bug_fix', animated: false },
  { id: 'e-perf-j', source: 'perf_analyzer', target: 'judge', animated: false },
  { id: 'e-bf-j', source: 'bug_fix', target: 'judge', animated: false },

  // Judge → Ops
  { id: 'e-j-cont', source: 'judge', target: 'container_agent', animated: false },
  { id: 'e-j-docs', source: 'judge', target: 'docs_agent', animated: false },
  { id: 'e-j-cicd', source: 'judge', target: 'cicd_agent', animated: false },
]

const edgeDefaults = {
  style: { stroke: 'rgba(139,92,246,0.25)', strokeWidth: 1.5 },
  type: 'smoothstep',
}

export default function SwarmCanvas() {
  const agents = useSwarmStore((s) => s.agents)

  // Animate edges whose source agent is running
  const edges = useMemo(() => {
    return initialEdges.map((e) => ({
      ...e,
      ...edgeDefaults,
      animated: agents[e.source]?.status === 'running',
      style: {
        ...edgeDefaults.style,
        stroke: agents[e.source]?.status === 'running'
          ? '#8b5cf6'
          : agents[e.source]?.status === 'done'
            ? 'rgba(16,185,129,0.4)'
            : 'rgba(139,92,246,0.15)',
        strokeWidth: agents[e.source]?.status === 'running' ? 2 : 1.5,
      },
    }))
  }, [agents])

  return (
    <div style={{ width: '100%', height: '100%', background: 'var(--bg-primary)' }}>
      <ReactFlow
        nodes={initialNodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        zoomOnScroll={true}
        panOnScroll={true}
        minZoom={0.3}
        maxZoom={1.5}
      >
        <Background color="rgba(139,92,246,0.05)" gap={20} size={1} />
        <Controls
          style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}
          showInteractive={false}
        />
        <MiniMap
          style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)' }}
          nodeColor={(n) => {
            const type = n.data?.type
            const map = { META: '#8b5cf6', DEV: '#10b981', QA: '#ef4444', OPS: '#3b82f6', JUDGE: '#f59e0b' }
            return map[type] || '#5a5a7a'
          }}
          maskColor="rgba(0,0,0,0.7)"
        />
      </ReactFlow>
    </div>
  )
}
