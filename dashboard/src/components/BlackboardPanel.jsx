import React, { useState, useEffect } from 'react'
import { useSwarmStore } from '../store/swarmStore'
import { getBlackboard, getFileContent } from '../api'
import CodeViewer from './CodeViewer'
import { FileCode, Database, Globe, ChevronRight, Folder } from 'lucide-react'

export default function BlackboardPanel() {
  const activeSession = useSwarmStore((s) => s.activeSession)
  const blackboard = useSwarmStore((s) => s.blackboard)
  const setBlackboard = useSwarmStore((s) => s.setBlackboard)

  const [tab, setTab] = useState('spec')
  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState('')

  useEffect(() => {
    if (activeSession?.id && !blackboard) {
      getBlackboard(activeSession.id).then(setBlackboard).catch(() => {})
    }
  }, [activeSession?.id])

  const handleFileClick = async (file) => {
    setSelectedFile(file)
    if (activeSession) {
      try {
        const data = await getFileContent(activeSession.id, file.file_path)
        setFileContent(data.content)
      } catch {
        setFileContent(file.content || '// File content unavailable')
      }
    }
  }

  const tabs = ['spec', 'architecture', 'files', 'tests']

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', animation: 'fadeIn 0.3s' }}>
      {/* Sub-tabs */}
      <div style={{ display: 'flex', gap: 2, marginBottom: 12 }}>
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: '6px 14px', borderRadius: 'var(--radius-sm)',
              background: tab === t ? 'var(--accent-purple-dim)' : 'transparent',
              color: tab === t ? 'var(--accent-purple)' : 'var(--text-secondary)',
              border: 'none', cursor: 'pointer', fontSize: '0.8rem',
              fontWeight: 500, fontFamily: 'var(--font-sans)',
              transition: 'all var(--transition-fast)',
            }}>
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {/* SPEC TAB */}
        {tab === 'spec' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Raw Prompt */}
            {activeSession?.raw_spec && (
              <div className="glass" style={{ padding: 14, borderLeft: '3px solid var(--accent-purple)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Original Prompt
                  </h3>
                  <button className="btn btn-sm btn-secondary" style={{ fontSize: '0.7rem' }}
                    onClick={() => navigator.clipboard.writeText(activeSession.raw_spec)}>
                    Copy Text
                  </button>
                </div>
                <textarea
                  readOnly
                  value={activeSession.raw_spec}
                  style={{
                    width: '100%', minHeight: 80, fontSize: '0.85rem', color: 'var(--text-primary)',
                    background: 'var(--bg-card)', border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-sm)', padding: 8, resize: 'vertical'
                  }}
                />
                <div style={{ marginTop: 10, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <Folder size={12} style={{ display: 'inline', marginRight: 4 }} />
                  Files are generated locally in: <strong>./output/</strong>
                </div>
              </div>
            )}

            {blackboard?.spec ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {(blackboard.spec.goals || []).map((g, i) => (
              <div key={i} className="glass" style={{ padding: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{g.id || `G${i+1}`}</span>
                  <span style={{ fontWeight: 500, fontSize: '0.85rem' }}>{g.title}</span>
                  <span className={`badge ${g.priority === 'HIGH' ? 'badge-danger' : g.priority === 'LOW' ? 'badge-info' : 'badge-warning'}`}>
                    {g.priority}
                  </span>
                </div>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 8 }}>
                  {g.description}
                </p>
                <div style={{ fontSize: '0.75rem' }}>
                  {(g.acceptance_criteria || []).map((c, j) => (
                    <div key={j} style={{ color: 'var(--text-muted)', padding: '2px 0' }}>
                      ✓ {c}
                    </div>
                  ))}
                </div>
              </div>
            ))}
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                Spec not yet generated...
              </div>
            )}
          </div>
        )}

        {/* ARCHITECTURE TAB */}
        {tab === 'architecture' && blackboard?.architecture && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Tech Stack Chips */}
            <div>
              <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 8, color: 'var(--accent-purple)' }}>
                Tech Stack
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {Object.entries(blackboard.architecture.tech_stack || {}).map(([k, v]) => (
                  <span key={k} className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                    {k}: {typeof v === 'object' ? v.framework || v.language || JSON.stringify(v) : v}
                  </span>
                ))}
              </div>
            </div>

            {/* Components */}
            <div>
              <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 8, color: 'var(--accent-green)' }}>
                Components ({(blackboard.architecture.components || []).length})
              </h3>
              {(blackboard.architecture.components || []).map((c, i) => (
                <div key={i} style={{
                  padding: '8px 12px', background: 'var(--bg-card)',
                  borderRadius: 'var(--radius-sm)', marginBottom: 4,
                  fontSize: '0.8rem', border: '1px solid var(--border)',
                }}>
                  <strong>{c.name}</strong> ({c.type}) — {c.responsibility}
                </div>
              ))}
            </div>

            {/* API Endpoints */}
            <div>
              <h3 style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 8, color: 'var(--accent-yellow)' }}>
                API Endpoints ({(blackboard.architecture.api_contracts || []).length})
              </h3>
              <div style={{
                background: 'var(--bg-card)', borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)', overflow: 'hidden',
              }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      <th style={{ padding: '8px 12px', textAlign: 'left', color: 'var(--text-muted)' }}>Method</th>
                      <th style={{ padding: '8px 12px', textAlign: 'left', color: 'var(--text-muted)' }}>Path</th>
                      <th style={{ padding: '8px 12px', textAlign: 'left', color: 'var(--text-muted)' }}>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(blackboard.architecture.api_contracts || []).map((ep, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '6px 12px' }}>
                          <span className="badge badge-info" style={{ fontSize: '0.6rem' }}>
                            {ep.method}
                          </span>
                        </td>
                        <td style={{ padding: '6px 12px', fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                          {ep.path}
                        </td>
                        <td style={{ padding: '6px 12px', color: 'var(--text-secondary)' }}>
                          {ep.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* FILES TAB */}
        {tab === 'files' && (
          <div style={{ display: 'flex', gap: 12, height: '100%' }}>
            {/* File tree */}
            <div style={{
              width: 240, overflow: 'auto',
              background: 'var(--bg-card)', borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)', padding: '8px 0',
            }}>
              {(blackboard?.files || []).map((f, i) => (
                <div key={i} onClick={() => handleFileClick(f)}
                  style={{
                    padding: '6px 14px', cursor: 'pointer', fontSize: '0.75rem',
                    fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)',
                    background: selectedFile?.file_path === f.file_path ? 'var(--accent-purple-dim)' : 'transparent',
                    display: 'flex', alignItems: 'center', gap: 6,
                    transition: 'background var(--transition-fast)',
                  }}>
                  <FileCode size={12} />
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {f.file_path}
                  </span>
                  {f.review_score > 0 && (
                    <span style={{
                      marginLeft: 'auto', fontSize: '0.65rem', fontWeight: 600,
                      color: f.review_score >= 80 ? 'var(--accent-green)' : 'var(--accent-yellow)',
                    }}>
                      {f.review_score.toFixed(0)}
                    </span>
                  )}
                </div>
              ))}
              {(!blackboard?.files || blackboard.files.length === 0) && (
                <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  No files generated yet
                </div>
              )}
            </div>

            {/* Code viewer */}
            <div style={{ flex: 1 }}>
              {selectedFile ? (
                <CodeViewer
                  content={fileContent || selectedFile.content}
                  language={selectedFile.language}
                  filePath={selectedFile.file_path}
                  reviewScore={selectedFile.review_score}
                />
              ) : (
                <div style={{
                  height: '100%', display: 'flex', alignItems: 'center',
                  justifyContent: 'center', color: 'var(--text-muted)',
                  fontSize: '0.85rem',
                }}>
                  Select a file to view
                </div>
              )}
            </div>
          </div>
        )}

        {/* TESTS TAB */}
        {tab === 'tests' && (
          <div>
            {(blackboard?.tests || []).length > 0 ? (
              <div style={{
                background: 'var(--bg-card)', borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)', overflow: 'hidden',
              }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      <th style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)' }}>Type</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)' }}>Coverage</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)' }}>Passed</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)' }}>Failed</th>
                      <th style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)' }}>Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {blackboard.tests.map((t, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                        <td style={{ padding: '8px 14px' }}>
                          <span className="badge badge-info">{t.test_type}</span>
                        </td>
                        <td style={{ padding: '8px 14px', fontFamily: 'var(--font-mono)' }}>
                          {t.coverage_pct?.toFixed(1) || '—'}%
                        </td>
                        <td style={{ padding: '8px 14px', color: 'var(--accent-green)' }}>
                          {t.tests_passed ?? '—'}
                        </td>
                        <td style={{ padding: '8px 14px', color: t.tests_failed > 0 ? 'var(--accent-red)' : 'var(--text-muted)' }}>
                          {t.tests_failed ?? '—'}
                        </td>
                        <td style={{ padding: '8px 14px', fontWeight: 600 }}>
                          {t.score?.toFixed(1) || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>
                No test results yet
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
