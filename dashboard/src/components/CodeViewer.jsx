import React from 'react'
import Editor from '@monaco-editor/react'

export default function CodeViewer({ content, language, filePath, reviewScore }) {
  const langMap = {
    python: 'python', javascript: 'javascript', typescript: 'typescript',
    jsx: 'javascript', tsx: 'typescript', yaml: 'yaml', yml: 'yaml',
    json: 'json', css: 'css', html: 'html', markdown: 'markdown',
    dockerfile: 'dockerfile', sql: 'sql', sh: 'shell', bash: 'shell',
  }

  const ext = filePath?.split('.').pop()?.toLowerCase() || ''
  const monacoLang = langMap[language] || langMap[ext] || 'plaintext'

  const scoreColor = reviewScore >= 80
    ? 'var(--accent-green)'
    : reviewScore >= 60
      ? 'var(--accent-yellow)'
      : 'var(--accent-red)'

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
    }}>
      {/* Header bar */}
      <div style={{
        padding: '8px 14px', background: 'var(--bg-card)',
        borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        fontSize: '0.8rem',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
            {filePath || 'untitled'}
          </span>
          <span className="badge badge-info" style={{ fontSize: '0.6rem' }}>
            {monacoLang.toUpperCase()}
          </span>
        </div>
        {reviewScore !== undefined && reviewScore !== null && (
          <span style={{
            fontFamily: 'var(--font-mono)', fontWeight: 600,
            color: scoreColor, fontSize: '0.8rem',
          }}>
            Score: {reviewScore.toFixed(0)}
          </span>
        )}
      </div>

      {/* Monaco Editor */}
      <div style={{ flex: 1 }}>
        <Editor
          height="100%"
          language={monacoLang}
          value={content || '// No content'}
          theme="vs-dark"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            padding: { top: 8 },
            renderLineHighlight: 'none',
            overviewRulerLanes: 0,
            hideCursorInOverviewRuler: true,
          }}
        />
      </div>
    </div>
  )
}
