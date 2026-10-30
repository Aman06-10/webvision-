import { useState } from 'react'
import { appealApi, type ReplyReview as RR } from './api'
import { IssueList } from './tools'
import { useT, type Key } from './i18n'

export default function ReplyReview({ onUse }: { onUse: (grounds: string[]) => void }) {
  const { t } = useT()
  const [text, setText] = useState('')
  const [res, setRes] = useState<RR | null>(null)
  const [busy, setBusy] = useState(false)
  const run = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    try { setRes(await appealApi.reviewReply(text)) } finally { setBusy(false) }
  }
  return (
    <section className="rise" aria-labelledby="rr-h">
      <h2 id="rr-h" className="sec-title">{t('r_title')}</h2>
      <p className="lede">{t('r_sub')}</p>
      <div className="cols">
        <form className="col" onSubmit={run}>
          <label className="field"><span>{t('r_ph')}</span>
            <textarea rows={10} value={text} onChange={e => setText(e.target.value)} maxLength={6000} />
          </label>
          <button className="btn btn-primary" type="submit" disabled={busy || !text.trim()}>{t('r_btn')}</button>
        </form>
        <div className="col" aria-live="polite">
          {res && (
            <div className="rise">
              <h3>{t('r_clauses')}</h3>
              {res.clauses.length === 0 && res.other_sections.length === 0 && <p className="muted">{t('r_none')}</p>}
              {[...res.clauses.map(c => ({ ...c, sub: c.title })), ...res.other_sections.map(o => ({ ...o, sub: o.title }))].map(c => (
                <div key={c.ref} className="clause"><strong>Section {c.ref}</strong> <span className="muted">{c.sub}</span><p>{c.summary}</p></div>
              ))}
              {res.flags.length > 0 && <>
                <h3>{t('r_flags')}</h3>
                <IssueList issues={res.flags.map(f => ({ code: f.code, level: 'warning' as const, message: f.message }))} />
              </>}
              {res.suggested_grounds.length > 0 && <>
                <h3>{t('r_grounds')}</h3>
                <div className="chips">{res.suggested_grounds.map(g => <span key={g} className="chip chip-static">{t(`g_${g}` as Key)}</span>)}</div>
                <button type="button" className="btn btn-sm" style={{ marginTop: 12 }} onClick={() => onUse(res.suggested_grounds)}>{t('r_use')}</button>
              </>}
              <p className="small muted disc">{t('r_disc')}</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
