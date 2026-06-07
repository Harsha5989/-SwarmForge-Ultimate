import React, { useState, useEffect, useRef } from 'react'
import { useSwarmStore } from '../store/swarmStore'
import { getFileContent, saveFileContent } from '../api'
import Editor from '@monaco-editor/react'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
import { FileCode, Save, Terminal as TerminalIcon } from 'lucide-react'

export default function WorkspacePanel() {
  const activeSession = useSwarmStore((s) => s.activeSession)
  const blackboard = useSwarmStore((s) => s.blackboard)

  const [selectedFile, setSelectedFile] = useState(null)
  const [fileContent, setFileContent] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  
  const terminalRef = useRef(null)
  const xtermRef = useRef(null)
  const wsRef = useRef(null)

  // Load file content when selected
  const handleFileClick = async (file) => {
    setSelectedFile(file)
    if (activeSession) {
      try {
        const data = await getFileContent(activeSession.id, file.file_path)
        setFileContent(data.content || '')
      } catch {
        setFileContent('// File content unavailable')
      }
    }
  }

  // Save file content
  const handleSave = async () => {
    if (!selectedFile || !activeSession) return
    setIsSaving(true)
    try {
      await saveFileContent(activeSession.id, selectedFile.file_path, fileContent)
    } catch (err) {
      console.error('Failed to save file', err)
      alert('Failed to save file.')
    } finally {
      setIsSaving(false)
    }
  }

  // Initialize Terminal
  useEffect(() => {
    if (!terminalRef.current || !activeSession) return

    const term = new Terminal({
      theme: { background: '#1e1e1e', foreground: '#d4d4d4' },
      fontFamily: 'monospace',
      fontSize: 13,
      cursorBlink: true,
    })
    
    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(terminalRef.current)
    fitAddon.fit()
    xtermRef.current = term

    // Connect WebSocket
    const wsUrl = `ws://${window.location.host}/api/v1/ws/terminal/${activeSession.id}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      term.writeln('\x1b[32m[SwarmForge] Connected to Sandbox Terminal\x1b[0m')
    }

    ws.onmessage = (event) => {
      term.write(event.data)
    }

    ws.onclose = () => {
      term.writeln('\x1b[31m[SwarmForge] Terminal Disconnected\x1b[0m')
    }

    term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(data)
      }
    })

    const handleResize = () => fitAddon.fit()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      ws.close()
      term.dispose()
    }
  }, [activeSession?.id])

  return (
    <div style={{ height: '100%', display: 'flex', gap: 12, animation: 'fadeIn 0.3s' }}>
      
      {/* File Tree */}
      <div style={{
        width: 240, overflow: 'auto',
        background: 'var(--bg-card)', borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border)', padding: '8px 0',
      }}>
        <div style={{ padding: '0 14px 8px', fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', borderBottom: '1px solid var(--border)', marginBottom: 8 }}>
          GENERATED FILES
        </div>
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
          </div>
        ))}
        {(!blackboard?.files || blackboard.files.length === 0) && (
          <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
            No files available. Run a session first.
          </div>
        )}
      </div>

      {/* Editor & Terminal Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
        
        {/* Editor */}
        <div style={{
          flex: 1, background: 'var(--bg-card)', borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden'
        }}>
          {/* Editor Header */}
          <div style={{ 
            height: 36, borderBottom: '1px solid var(--border)', display: 'flex', 
            alignItems: 'center', justifyContent: 'space-between', padding: '0 12px',
            background: 'var(--bg-secondary)'
          }}>
            <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
              {selectedFile ? selectedFile.file_path : 'No file selected'}
            </div>
            <button 
              className="btn btn-sm btn-primary" 
              onClick={handleSave} 
              disabled={!selectedFile || isSaving}
              style={{ display: 'flex', alignItems: 'center', gap: 4, height: 24, fontSize: '0.75rem' }}
            >
              <Save size={12} />
              {isSaving ? 'Saving...' : 'Save File'}
            </button>
          </div>
          
          {/* Monaco Editor */}
          <div style={{ flex: 1 }}>
            {selectedFile ? (
              <Editor
                height="100%"
                language={selectedFile.language || 'python'}
                theme="vs-dark"
                value={fileContent}
                onChange={(val) => setFileContent(val || '')}
                options={{
                  minimap: { enabled: false },
                  fontSize: 13,
                  fontFamily: 'monospace',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  padding: { top: 16 }
                }}
              />
            ) : (
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Select a file from the list to edit
              </div>
            )}
          </div>
        </div>

        {/* Terminal */}
        <div style={{
          height: '35%', background: '#1e1e1e', borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <div style={{ 
            height: 28, background: '#252526', display: 'flex', alignItems: 'center', 
            padding: '0 12px', gap: 6, fontSize: '0.7rem', color: '#ccc',
            borderBottom: '1px solid #333'
          }}>
            <TerminalIcon size={12} /> Sandbox Terminal
          </div>
          <div ref={terminalRef} style={{ flex: 1, padding: '8px', overflow: 'hidden' }} />
        </div>
      </div>
    </div>
  )
}
