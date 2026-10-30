import { useEffect, useMemo, useRef, useState } from 'react'
import { api, appealApi, ApiError, type Application, type AuthorityResult, type Issue, type Lang, type Reminders } from './api'
import { speak, speechSupported, startBrowserSpeech, startRecording } from './audio'
import Stamp from './Stamp'
import { useT, fmt, type Key } from './i18n'
import { IssueList, download } from './tools'
import { Confetti } from './Reveal'
import { TEMPLATES } from './templates'

const MAX = 3000
// Real RTI Online text-box rule (rtionline.gov.in guidelines): A-Z a-z 0-9 and , . - _ ( ) / @ : & ? \ %
const BAD = /[^A-Za-z0-9 \n\t,.\-_()/@:&?\\%]/g
const NON_ASCII = /[^\x00-\x7F]/
const EDITABLE = ['DRAFT', 'PAYMENT_FAILED']
const reduced = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

type Props = { email: string; setEmail: (e: string) => void; resume: Application | null }

const over0 = (s: string) => s.length > MAX

function Speaker() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 9v6h4l5 4V5L8 9H4z" /><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12" />
    </svg>
  )
}

function Check() {
  return (
    <svg className="check" viewBox="0 0 24 24" aria-hidden>
      <circle cx="12" cy="12" r="10.5" /><path d="M7 12.5l3.2 3.2L17 9" />
    </svg>
  )
}

export default function RequestFlow({ email, setEmail, resume }: Props) {
  const { t, lang } = useT()
  const [app, setApp] = useState<Application | null>(resume)
  const [emailDraft, setEmailDraft] = useState(email)
  const [langs, setLangs] = useState<Record<string, Lang>>({})
  const [stt, setStt] = useState(false)
  const [quality, setQuality] = useState<'verified' | 'beta'>('verified')
  const [step, setStep] = useState(1)

  const [src, setSrc] = useState('hi')
  const [target, setTarget] = useState<'en' | 'hi'>('en')
  const [original, setOriginal] = useState('')
  const [draft, setDraft] = useState(resume?.draft ?? '')
  const [via, setVia] = useState('')
  const [fresh, setFresh] = useState(false)
  const [revealing, setRevealing] = useState(false)
  const [busy, setBusy] = useState('')
  const [notice, setNotice] = useState('')
  const [saveState, setSaveState] = useState<'' | 'saving' | 'saved'>('')

  const [rec, setRec] = useState<null | { stop: () => unknown }>(null)
  const [auth, setAuth] = useState<AuthorityResult | null>(null)
  const [authList, setAuthList] = useState<{ key: string; name: string; name_hi?: string; level: string }[]>([])
  const [chosen, setChosen] = useState('')
  const [scenario, setScenario] = useState('success')
  const [hints, setHints] = useState<Issue[]>([])
  const [rem, setRem] = useState<Reminders | null>(null)
  const [jump, setJump] = useState(0)
  const [att, setAtt] = useState<{ ok: boolean; issues: Issue[] } | null>(null)
  const [bpl, setBpl] = useState(false)
  const payKey = useRef(crypto.randomUUID())
  const timer = useRef<number>()

  useEffect(() => {
    api.languages().then(setLangs).catch(() => {})
    api.health().then(h => setStt(h.stt)).catch(() => {})
    api.authorities().then(setAuthList).catch(() => {})
    if (resume) {
      api.get(resume.id).then(a => {
        setApp(a); setDraft(a.draft)
        if (a.authority_key) setChosen(a.authority_key)
        if (a.state !== 'DRAFT') setStep(3)
      })
    }
  }, [resume])

  const editable = !!app && EDITABLE.includes(app.state)
  const bad = useMemo(() => (target === 'en' ? [...new Set(draft.match(BAD) ?? [])] : []), [draft, target])
  const needsPdf = over0(draft) || (target === 'hi' && NON_ASCII.test(draft))
  const over = draft.length - MAX
  const draftOk = draft.trim().length > 0 && bad.length === 0 && !revealing
  const confirmed = !!app?.authority_confirmed
  const reach = confirmed ? 3 : draftOk ? 2 : 1

  useEffect(() => {
    if (!app || !editable || revealing) return
    setSaveState('saving')
    const h = setTimeout(() => {
      api.saveDraft(app.id, draft, src, original).then(() => setSaveState('saved')).catch(() => setSaveState(''))
    }, 1200)
    return () => clearTimeout(h)
  }, [draft, original, src, app?.id, editable, revealing])

  useEffect(() => {
    if (!app || app.state !== 'PAYMENT_PENDING') return
    const h = setInterval(() => api.get(app.id).then(setApp).catch(() => {}), 2000)
    return () => clearInterval(h)
  }, [app?.id, app?.state])

  useEffect(() => { if (app?.state === 'PAYMENT_FAILED') payKey.current = crypto.randomUUID() }, [app?.state])

  // wording hints, English drafts only (the checks look for English phrases)
  useEffect(() => {
    if (target !== 'en' || revealing || draft.trim().length < 15) { setHints([]); return }
    const h = setTimeout(() => appealApi.hints(draft).then(r => setHints(r.hints)).catch(() => {}), 900)
    return () => clearTimeout(h)
  }, [draft, target, revealing])

  // reminders after submission; `jump` moves "today" forward for the demo
  useEffect(() => {
    if (!app || app.state !== 'SUBMITTED') return
    const d = new Date(Date.now() + jump * 864e5).toISOString().slice(0, 10)
    appealApi.reminders(app.id, jump ? d : undefined).then(setRem).catch(() => {})
  }, [app?.id, app?.state, jump])

  // entering step 2 looks up the authority on its own
  useEffect(() => {
    if (step === 2 && !auth && draftOk && !confirmed) findAuth()
  }, [step])

  const fail = (e: unknown) => setNotice(
    e instanceof ApiError && e.status === 503 ? t('svc_busy')
      : e instanceof ApiError && typeof e.detail === 'string' ? e.detail : t('err'))

  function reveal(text: string) {
    window.clearInterval(timer.current)
    setFresh(true)
    if (reduced()) { setDraft(text); return }
    setRevealing(true)
    const stepSize = Math.max(1, Math.ceil(text.length / 80))
    let i = 0
    timer.current = window.setInterval(() => {
      i += stepSize
      setDraft(text.slice(0, i))
      if (i >= text.length) { window.clearInterval(timer.current); setRevealing(false) }
    }, 16)
  }
  useEffect(() => () => window.clearInterval(timer.current), [])

  async function begin(ev: React.FormEvent) {
    ev.preventDefault()
    try { const a = await api.create(emailDraft.trim()); setEmail(a.email); setApp(a) } catch (e) { fail(e) }
  }

  async function toDraft(text: string) {
    setBusy('working'); setNotice('')
    try {
      const r = await api.translate(text, src, target)
      reveal(r.translated); setVia(r.engine === 'none' ? '' : r.engine); setQuality(r.quality ?? 'verified')
    } catch (e) { fail(e) } finally { setBusy('') }
  }

  async function toggleMic() {
    setNotice('')
    if (rec) { await rec.stop(); setRec(null); return }
    try {
      if (stt) {
        const r = await startRecording()
        setRec({ stop: async () => {
          setBusy('working')
          try {
            const out = await api.transcribe(await r.stop(), src, target)
            setOriginal(out.original); reveal(out.translated); setVia(out.engine); setQuality(out.quality ?? 'verified')
          } catch (e) { fail(e) } finally { setBusy('') }
        } })
      } else if (speechSupported()) {
        let latest = ''
        setRec(startBrowserSpeech(src, txt => { latest = txt; setOriginal(txt) }, () => {
          setRec(null); if (latest) toDraft(latest)
        }))
      } else setNotice(t('no_speech'))
    } catch { setNotice(t('mic_denied')) }
  }

  async function tidy() {
    setBusy('working')
    try { const r = await api.refine(draft); reveal(r.draft); setVia('nvidia-llm') } catch (e) { fail(e) } finally { setBusy('') }
  }

  async function findAuth() {
    setBusy('auth'); setNotice('')
    try { const r = await api.findAuthority(draft); setAuth(r); setChosen(r.key === 'unknown' || r.confidence < 0.45 ? '' : r.key) }
    catch (e) { fail(e) } finally { setBusy('') }
  }

  async function confirmAuth() {
    if (!app || !chosen) return
    try { await api.confirmAuthority(app.id, chosen); setApp(await api.get(app.id)); setStep(3) } catch (e) { fail(e) }
  }

  async function pay() {
    if (!app) return
    setBusy('paying'); setNotice('')
    try { await api.pay(app.id, payKey.current, scenario) } catch (e) { fail(e) }
    try { setApp(await api.get(app.id)) } finally { setBusy('') }
  }

  if (!app) {
    return (
      <section className="start rise" aria-labelledby="start-h">
        <div className="start-art" aria-hidden>
          <span /><span /><span />
        </div>
        <h1 id="start-h" className="page-title">{t('start_h')}</h1>
        <p className="lede">{t('start_p')}</p>
        <form onSubmit={begin} className="row-form">
          <label className="field"><span>{t('email')}</span>
            <input type="email" required autoComplete="email" value={emailDraft} onChange={e => setEmailDraft(e.target.value)} />
          </label>
          <button className="btn btn-primary" type="submit">{t('start')}</button>
        </form>
        {notice && <p role="alert" className="note bad">{notice}</p>}
      </section>
    )
  }

  const hi = lang === 'hi'
  const nm = (o: { name: string; name_hi?: string }) => (hi && o.name_hi) || o.name
  const confLabel = (c: number) => (c >= 0.7 ? t('high') : c >= 0.45 ? t('medium') : t('low'))
  const locked = !editable
  const authObj = authList.find(a => a.key === (app.authority_key ?? chosen))
  const authName = authObj && nm(authObj)
  const receiptText = () => [
    'RTI REQUEST RECEIPT (redesign demo: nothing was actually filed)', '',
    `Registration number: ${app.rti_number ?? ''}`,
    ...(app.children ?? []).map(k => `Also forwarded as: ${k.rti_number}`),
    `Office: ${authObj?.name ?? ''}`, `Fee: Rs 10 (simulated)`,
    `Saved on: ${new Date().toISOString().slice(0, 10)}`, '', 'Request text:', draft, '',
    'Keep your own copy. The official portal keeps a request for 3 years.',
  ].join('\n')
  const stepsMeta = [1, 2, 3] as const

  // payment timeline state
  const st = app.state
  const tl = [
    { k: 'tl_start', s: st === 'DRAFT' ? (busy === 'paying' ? 'active' : 'todo') : 'done' },
    { k: 'tl_bank', s: st === 'SUBMITTED' ? 'done' : st === 'PAYMENT_PENDING' ? 'active' : st === 'PAYMENT_FAILED' ? 'failed' : 'todo' },
    { k: 'tl_done', s: st === 'SUBMITTED' ? 'done' : 'todo' },
  ]

  return (
    <div className="flow">
      {busy && <div className="topbar" aria-hidden />}

      <nav className="stepper" aria-label="Progress">
        {stepsMeta.map(n => {
          const done = n < step || (n === 3 && st === 'SUBMITTED')
          const cls = done ? 'done' : n === step ? 'current' : n <= reach ? 'open' : 'todo'
          return (
            <button key={n} className={`st ${cls}`} disabled={n > reach} onClick={() => setStep(n)} aria-current={n === step ? 'step' : undefined}>
              <span className="st-dot">{done ? <Check /> : n}</span>
              <span className="st-label">{t(`step_${n}` as Key)}</span>
            </button>
          )
        })}
        <div className="st-line" style={{ ['--p' as string]: `${((Math.min(step, 3) - 1) / 2) * 100}%` }} aria-hidden />
        <div className="st-meta">
          <div className="mono small muted">#{String(app.id).padStart(4, '0')}</div>
          <Stamp state={app.state} />
        </div>
      </nav>

      <div className="panel" key={step}>
        {/* STEP 1 */}
        {step === 1 && (
          <section aria-labelledby="h1" className="rise">
            <h1 id="h1" className="page-title">{t('s1')}</h1>
            <p className="lede">{t('s1_p')}</p>

            <div className="cols">
              <div className="col">
                <div className="pair">
                  <label className="field"><span>{t('speak_lang')}</span>
                    <select value={src} onChange={e => setSrc(e.target.value)} disabled={locked}>
                      {Object.entries(langs).map(([k, v]) => <option key={k} value={k}>{v.name}{v.quality === 'beta' ? ` (${t('beta')})` : ''}</option>)}
                    </select>
                  </label>
                  <label className="field"><span>{t('draft_lang')}</span>
                    <select value={target} onChange={e => setTarget(e.target.value as 'en' | 'hi')} disabled={locked}>
                      <option value="en">English</option><option value="hi">हिन्दी</option>
                    </select>
                  </label>
                </div>

                <div className="voice">
                  <button type="button" className={rec ? 'mic recording' : 'mic'} onClick={toggleMic}
                    disabled={locked || busy === 'working'} aria-pressed={!!rec} aria-label={rec ? t('stop') : t('speak')}>
                    <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                      <rect x="9" y="3" width="6" height="11" rx="3" /><path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
                    </svg>
                  </button>
                  <div className="voice-text" aria-live="polite">
                    <strong>{rec ? t('stop') : t('speak')}</strong>
                    <span className="muted">{rec ? t('listening') : busy === 'working' ? t('working') : t('or_type')}</span>
                  </div>
                  <div className={rec ? 'wave on' : 'wave'} aria-hidden>
                    {Array.from({ length: 9 }, (_, i) => <span key={i} style={{ ['--i' as string]: i }} />)}
                  </div>
                </div>

                <label className="field"><span>{t('your_words')}</span>
                  <textarea rows={6} value={original} onChange={e => setOriginal(e.target.value)} disabled={locked} lang={src} />
                </label>
                {!locked && !original.trim() && (
                  <div className="examples">
                    <div className="small muted">{t('tpl_h')}</div>
                    <div className="chips">
                      {TEMPLATES.map(x => (
                        <button key={x.id} type="button" className="chip" onClick={() => setOriginal(src === 'hi' ? x.hi : x.en)}>{x.label[lang === 'hi' ? 'hi' : 'en']}</button>
                      ))}
                    </div>
                    <div className="small muted">{t('tpl_note')}</div>
                  </div>
                )}
                <button className="btn" type="button" onClick={() => toDraft(original)} disabled={locked || !original.trim() || !!busy}>
                  {t('make_draft')} <span aria-hidden>→</span>
                </button>
              </div>

              <div className="col">
                <div className={fresh && !revealing ? 'sheet flash' : 'sheet'} onAnimationEnd={() => setFresh(false)}>
                  <div className="sheet-head">
                    <span>{t('official')} · {target === 'en' ? 'English' : 'हिन्दी'}</span>
                    <span className="small muted" aria-live="polite">{saveState === 'saving' ? t('saving') : saveState === 'saved' ? t('saved') : ''}</span>
                  </div>
                  <textarea className="paper" rows={11} value={draft} readOnly={revealing}
                    onChange={e => { setDraft(e.target.value); setVia('') }} disabled={locked} aria-label={t('official')} lang={target} />
                  <div className="sheet-foot">
                    <span className={over > 0 ? 'mono small warn-t' : 'mono small'}>{draft.length} / {MAX} {t('counter')}</span>
                    {via && <span className="small muted">{t('via')}: {via}</span>}
                    <button className="btn btn-quiet btn-sm" type="button" onClick={() => navigator.clipboard?.writeText(draft)} disabled={!draft.trim()}>{t('copy_req')}</button>
                    <button className="btn btn-quiet btn-sm" type="button" onClick={() => speak(draft, target, api.speak)} disabled={!draft.trim() || revealing} aria-label={t('listen')}><Speaker />{t('listen')}</button>
                    <button className="btn btn-quiet btn-sm" type="button" onClick={tidy} disabled={locked || !draft.trim() || !!busy}>{t('tidy')}</button>
                  </div>
                </div>
                {over > 0 && <p role="status" className="note warn">{t('attach_long')}</p>}
                {target === 'hi' && NON_ASCII.test(draft) && <p role="status" className="note warn">{t('hi_attach')}</p>}
                {bad.length > 0 && (
                  <p role="alert" className="note bad">
                    {t('bad_chars')} <span className="mono">{bad.join(' ')}</span>{' '}
                    <button type="button" className="link" onClick={() => api.sanitize(draft).then(r => setDraft(r.draft)).catch(() => setDraft(draft.replace(BAD, '')))}>{t('fix_auto')}</button>
                  </p>
                )}
                {quality === 'beta' && via && !revealing && <p className="note warn" role="alert">{t('beta_warn')}</p>}
                {via && !revealing && draftOk && quality === 'verified' && <p className="note ok" role="status">{t('draft_ready')}</p>}
                {target === 'en' && !revealing && draft.trim().length >= 15 && (
                  <div className="hints" aria-live="polite">
                    <div className="small muted">{t('hint_h')}</div>
                    {hints.length ? <IssueList issues={hints} /> : <p className="small ok-t">{t('hint_ok')}</p>}
                  </div>
                )}
              </div>
            </div>

            <div className="actions">
              <span />
              <button className="btn btn-primary" type="button" onClick={() => setStep(2)} disabled={!draftOk}>{t('next')} <span aria-hidden>→</span></button>
            </div>
          </section>
        )}

        {/* STEP 2 */}
        {step === 2 && (
          <section aria-labelledby="h2" className="rise">
            <h1 id="h2" className="page-title">{t('s2')}</h1>
            <p className="lede">{t('s2_p')}</p>

            {busy === 'auth' && <div className="skeleton" role="status"><span /><span /><span className="sr-only">{t('checking_auth')}</span></div>}

            {auth && busy !== 'auth' && auth.key !== 'unknown' && (
              <div className="result rise" aria-live="polite">
                <div className="small muted">{t('likely')}</div>
                <div className="result-name">{hi && auth.authority_hi ? auth.authority_hi : auth.authority}</div>
                {auth.portal && <div>{t('portal')}: <strong>{hi && auth.portal_hi ? auth.portal_hi : auth.portal}</strong></div>}
                <div className="meter" aria-label={`${t('conf')}: ${confLabel(auth.confidence)}`}>
                  <div className="meter-bar"><i style={{ ['--w' as string]: `${Math.max(6, auth.confidence * 100)}%` }} /></div>
                  <span className="small">{t('conf')}: <strong>{confLabel(auth.confidence)}</strong> · {auth.source}</span>
                </div>
                <div className="muted">{hi ? auth.reason.replace('Matched words:', 'मिले शब्द:') : auth.reason}</div>
              </div>
            )}
            {auth && busy !== 'auth' && (auth.key === 'unknown' || auth.confidence < 0.7) && (
              <div className="note warn" role="status">
                <strong>{t('unsure')}</strong>
                {auth.key === 'unknown' && <><br />{t('tip_detail')}</>}
              </div>
            )}
            {auth && busy !== 'auth' && auth.candidates.filter(c => c.key !== auth.key).length > 0 && (
              <div className="others">
                <div className="small muted">{t('other_offices')}</div>
                <div className="chips">
                  {auth.candidates.filter(c => c.key !== auth.key).map(c => (
                    <button key={c.key} type="button" className={chosen === c.key ? 'chip on' : 'chip'} onClick={() => setChosen(c.key)}>{nm(c)}</button>
                  ))}
                </div>
              </div>
            )}

            {(auth || confirmed) && busy !== 'auth' && (
              <>
                <label className="field narrow"><span>{t('change')}</span>
                  <select value={chosen} onChange={e => setChosen(e.target.value)} disabled={locked}>
                    <option value="" disabled>—</option>
                    {authList.map(a => <option key={a.key} value={a.key}>{nm(a)}</option>)}
                  </select>
                </label>
                {authList.find(a => a.key === chosen)?.level === 'state' && <p className="note warn" role="alert">{t('state_note2')}</p>}
              </>
            )}
            {!auth && !confirmed && busy !== 'auth' && (
              <button className="btn" type="button" onClick={findAuth}>{t('find')}</button>
            )}

            <div className="actions">
              <button className="btn btn-quiet" type="button" onClick={() => setStep(1)}><span aria-hidden>←</span> {t('back')}</button>
              <button className="btn btn-primary" type="button" onClick={confirmAuth} disabled={!chosen || locked}>{t('confirm')} <span aria-hidden>→</span></button>
            </div>
          </section>
        )}

        {/* STEP 3 */}
        {step === 3 && (
          <section aria-labelledby="h3" className="rise">
            <h1 id="h3" className="page-title">{t('s3')}</h1>
            <p className="lede">{t('s3_p')}</p>

            <div className="cols pay-cols">
              <div className="col">
                {st === 'SUBMITTED' ? (
                  <div className="receipt" role="status">
                    <Confetti />
                    <Check />
                    <h2>{t('done_h')}</h2>
                    <p className="muted">{t('done_p')}</p>
                    <div className="small muted">{t('number')} <button type="button" className="link" onClick={() => speak(`${t('number')}: ${(app.rti_number ?? '').replace(/\//g, ' ')}`, target, api.speak)}><Speaker />{t('listen')}</button></div>
                    <div className="rti-no" aria-label={app.rti_number ?? ''}>
                      {(app.rti_number ?? '').split('').map((c, i) => <span key={i} style={{ ['--i' as string]: i }}>{c}</span>)}
                    </div>
                    {(app.children?.length ?? 0) > 0 && (
                      <div className="kids">
                        <div className="small muted">{t('fw_title')}</div>
                        <ul className="mono small">
                          {app.children!.map(k => <li key={k.rti_number}>{k.rti_number}</li>)}
                        </ul>
                        <div className="small muted">{t('fw_note')}</div>
                      </div>
                    )}
                    <div className="out-actions">
                      <button type="button" className="btn btn-sm" onClick={() => download(`rti-${app.id}-receipt.txt`, receiptText())}>{t('rc_dl')}</button>
                      <button type="button" className="btn btn-sm" onClick={() => window.print()}>{t('rc_print')}</button>
                    </div>
                    <p className="small muted">{t('rc_note')}</p>
                    <pre className="printable paper-pre print-only" lang="en">{receiptText()}</pre>
                    <button type="button" className="link demo-link" onClick={() => appealApi.forward(app.id).then(() => api.get(app.id)).then(setApp)}>{t('fw_demo')}</button>
                  </div>
                ) : (
                  <>
                    <div className="bill">
                      <div><span className="muted">{t('fee')}</span><strong className="amt">₹10</strong></div>
                      <div className="small muted">{authName}</div>
                    </div>
                    {st === 'PAYMENT_PENDING' && (
                      <div className="note warn" role="status" aria-live="polite"><strong>{t('pending_h')}</strong><br />{t('pending_p')}</div>
                    )}
                    {st === 'PAYMENT_FAILED' && (
                      <div className="note bad" role="alert"><strong>{t('failed_h')}</strong><br />{t('failed_p')}</div>
                    )}
                    <details className="prepay">
                      <summary>{t('pp_title')}</summary>
                      <ul>{[1, 2, 3, 4, 5, 6, 7].map(n => <li key={n}>{t(`pp${n}` as Key)}</li>)}</ul>
                      <div className="small muted">{t('pp_src')}</div>
                    </details>
                    <details className="prepay">
                      <summary>{t('at_title')}</summary>
                      <p className="small muted">{t('at_sub')}</p>
                      <label className="choice"><input type="checkbox" checked={bpl} onChange={e => { setBpl(e.target.checked); setAtt(null) }} /><span>{t('at_bpl')}</span></label>
                      <input type="file" aria-label={t('at_pick')} onChange={e => {
                        const f = e.target.files?.[0]
                        if (f) appealApi.attachment(f.name, f.size, bpl ? 'bpl' : 'supporting').then(setAtt).catch(() => {})
                      }} />
                      {att && <IssueList issues={att.issues} />}
                    </details>
                    <label className="field demo"><span>{t('demo')}</span>
                      <select value={scenario} onChange={e => setScenario(e.target.value)}>
                        {['success', 'failure', 'timeout'].map(s => <option key={s} value={s}>{t(`sc_${s}` as Key)}</option>)}
                      </select>
                    </label>
                    <button className="btn btn-primary btn-big" type="button" onClick={pay}
                      disabled={!confirmed || !draftOk || !editable || busy === 'paying'}>
                      {busy === 'paying' ? t('paying') : t('pay')}
                    </button>
                  </>
                )}
              </div>

              <div className="col">
                <ol className="timeline" aria-label={t('history')}>
                  {tl.map(n => (
                    <li key={n.k} className={`tl ${n.s}`}>
                      <span className="tl-dot">{n.s === 'done' ? <Check /> : n.s === 'failed' ? '!' : ''}</span>
                      <span>{t(n.k as Key)}</span>
                    </li>
                  ))}
                </ol>
                {st === 'SUBMITTED' && (
                  <div className="reminders">
                    <h3>{t('rm_title')}</h3>
                    <p className="small muted">{t('rm_sub')}</p>
                    <ul>
                      {rem?.items.map(i => (
                        <li key={i.kind} className={`rm rm-${i.state}`}>
                          <span className="rm-date mono small">{i.date}</span>
                          <div><strong>{i.title}</strong><div className="small muted">{i.text}</div></div>
                          <em>{i.state === 'due' ? t('rm_due') : i.state === 'past' ? fmt(t('rm_past'), { n: -i.days }) : fmt(t('rm_in'), { n: i.days })}</em>
                        </li>
                      ))}
                    </ul>
                    <div className="jump">
                      <span className="small muted">{t('rm_jump')}</span>
                      {[0, 26, 31, 55].map(n => (
                        <button key={n} type="button" className={jump === n ? 'chip on' : 'chip'} onClick={() => setJump(n)}>{n === 0 ? t('rm_today') : `+${n} ${t('rm_days')}`}</button>
                      ))}
                    </div>
                  </div>
                )}
                {app.events && app.events.length > 0 && (
                  <details className="tape">
                    <summary>{t('history')}</summary>
                    <ol className="mono small">
                      {app.events.map((e, i) => <li key={i}><span className="muted">{e.at.slice(11, 19)}</span> {e.kind} {e.detail}</li>)}
                    </ol>
                  </details>
                )}
              </div>
            </div>

            <div className="actions">
              <button className="btn btn-quiet" type="button" onClick={() => setStep(2)} disabled={st !== 'DRAFT' && st !== 'PAYMENT_FAILED'}><span aria-hidden>←</span> {t('back')}</button>
              <span />
            </div>
          </section>
        )}

        {notice && <p role="alert" className="note bad">{notice}</p>}
      </div>
    </div>
  )
}
