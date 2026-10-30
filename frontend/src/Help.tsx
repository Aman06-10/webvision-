import { useState } from 'react'
import { api, type Answer } from './api'
import { speak } from './audio'
import { useT, type Key } from './i18n'

export default function Help() {
  const { t, lang } = useT()
  const [q, setQ] = useState('')
  const [out, setOut] = useState<Answer | null>(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(false)

  async function ask(question: string) {
    if (!question.trim()) return
    setBusy(true); setErr(false); setQ(question)
    try { setOut(await api.ask(question, lang)) } catch { setErr(true) } finally { setBusy(false) }
  }

  return (
    <section className="help rise" aria-labelledby="help-h">
      <h1 id="help-h" className="page-title">{t('help_h')}</h1>
      <p className="lede">{t('help_p')}</p>
      <form onSubmit={e => { e.preventDefault(); ask(q) }} className="row-form">
        <label className="field"><span>{t('help_h')}</span>
          <input value={q} onChange={e => setQ(e.target.value)} placeholder={t('ask_ph')} maxLength={500} />
        </label>
        <button className="btn btn-primary" type="submit" disabled={busy || !q.trim()}>{busy ? t('asking') : t('ask')}</button>
      </form>
      <div className="chips">
        {(['ex1', 'ex2', 'ex3'] as Key[]).map(k => <button key={k} type="button" className="chip" onClick={() => ask(t(k))}>{t(k)}</button>)}
      </div>
      {err && <p role="alert" className="note bad">{t('err')}</p>}
      {busy && <div className="skeleton" role="status"><span /><span /><span /></div>}
      {out && !busy && (
        <div className="answer rise" aria-live="polite">
          <p>{out.answer}</p>
          <button type="button" className="link" onClick={() => speak(out.answer, lang, api.speak)}>{t('listen')}</button>
          {out.sources.length > 0 && (
            <div className="small muted">{t('sources')}: {out.sources.map(s => s.title).join(' · ')}</div>
          )}
        </div>
      )}
    </section>
  )
}
