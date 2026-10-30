import { useState } from 'react'
import type { Issue } from './api'
import { strings, useT, type Key } from './i18n'

export function IssueList({ issues }: { issues: Issue[] }) {
  const { t, lang } = useT()
  if (!issues.length) return null
  const label = (i: Issue) => {
    const hi = lang === 'hi' ? (strings.hi as Record<string, string>)[`i_${i.code}`] : undefined
    return hi ?? i.message
  }
  return (
    <ul className="issues" role="list">
      {issues.map((i, n) => (
        <li key={i.code + n} className={`issue lvl-${i.level}`}>
          <span className="issue-tag">{t(`lvl_${i.level}` as Key)}</span>
          <div>
            <div>{label(i)}</div>
            {lang === 'hi' && label(i) !== i.message && <div className="small muted">{i.message}</div>}
          </div>
        </li>
      ))}
    </ul>
  )
}

export function download(name: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url; a.download = name; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function DraftOutput({ text, name, ready, issues }: { text: string; name: string; ready: boolean; issues: Issue[] }) {
  const { t } = useT()
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1600) } catch { /* ignore */ }
  }
  return (
    <div className="draft-out rise">
      <h3>{t('draft_h')}</h3>
      {issues.length > 0 && <><div className="small muted">{ready ? '' : t('draft_fix')}</div><IssueList issues={issues} /></>}
      {ready && <p className="note ok" role="status">{t('draft_ready')}</p>}
      <pre className="printable paper-pre" lang="en">{text}</pre>
      <div className="out-actions">
        <button type="button" className="btn btn-sm" onClick={copy}>{copied ? t('copied') : t('copy')}</button>
        <button type="button" className="btn btn-sm" onClick={() => download(name, text)}>{t('download')}</button>
        <button type="button" className="btn btn-sm" onClick={() => window.print()}>{t('print')}</button>
      </div>
    </div>
  )
}

type FieldProps = { label: string; value: string; onChange: (v: string) => void; type?: string; rows?: number; max?: string; hint?: string }
export function Field({ label, value, onChange, type = 'text', rows, max, hint }: FieldProps) {
  return (
    <label className="field"><span>{label}</span>
      {rows
        ? <textarea rows={rows} value={value} onChange={e => onChange(e.target.value)} />
        : <input type={type} value={value} max={max} onChange={e => onChange(e.target.value)} />}
      {hint && <small className="muted">{hint}</small>}
    </label>
  )
}

export function Check({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="choice"><input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} /><span>{label}</span></label>
  )
}
