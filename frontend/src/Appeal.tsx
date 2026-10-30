import { useState } from 'react'
import { ApiError, checkAppeal, type AppealResult } from './api'
import { fmt, useT, type Key } from './i18n'

const iso = (d: Date) => d.toISOString().slice(0, 10)
const ago = (n: number) => iso(new Date(Date.now() - n * 864e5))
const KEYS = ['reply_due', 'first_appeal_opens', 'first_appeal_deadline', 'fa_decision_due', 'second_appeal_opens', 'second_appeal_deadline']

export function AppealCheck({ initialFiled }: { initialFiled?: string }) {
  const { t, lang } = useT()
  const [filed, setFiled] = useState(initialFiled ?? ago(10))
  const [what, setWhat] = useState<'none' | 'reply' | 'transfer'>('none')
  const [replied, setReplied] = useState(ago(5))
  const [hasFa, setHasFa] = useState(false)
  const [faOn, setFaOn] = useState(ago(40))
  const [decided, setDecided] = useState(false)
  const [decOn, setDecOn] = useState(ago(5))
  const [res, setRes] = useState<AppealResult | null>(null)
  const [err, setErr] = useState(false)

  const dateFmt = (s: string) => new Date(s + 'T00:00:00').toLocaleDateString(lang === 'hi' ? 'hi-IN' : 'en-IN', { day: 'numeric', month: 'short', year: 'numeric' })

  async function run(over?: Partial<{ filed: string; what: typeof what; replied: string; hasFa: boolean; faOn: string; decided: boolean }>) {
    const v = { filed, what, replied, hasFa, faOn, decided, ...over }
    setErr(false)
    try {
      setRes(await checkAppeal({
        filed: v.filed,
        replied: v.what === 'reply' ? v.replied : undefined,
        transferred_physically: v.what === 'transfer',
        first_appeal: v.hasFa ? v.faOn : undefined,
        fa_decided: v.hasFa && v.decided ? decOn : undefined,
      }))
    } catch (e) { setRes(null); setErr(e instanceof ApiError) }
  }

  function example(n: 1 | 2 | 3 | 4) {
    const p = {
      1: { filed: ago(10), what: 'none' as const, hasFa: false },
      2: { filed: ago(45), what: 'none' as const, hasFa: false },
      3: { filed: ago(40), what: 'reply' as const, replied: ago(8), hasFa: false },
      4: { filed: ago(80), what: 'none' as const, hasFa: true, faOn: ago(40), decided: false },
    }[n]
    setFiled(p.filed); setWhat(p.what); setHasFa(p.hasFa)
    if ('replied' in p && p.replied) setReplied(p.replied)
    if ('faOn' in p && p.faOn) setFaOn(p.faOn)
    setDecided(false)
    run(p)
  }

  const stageKey = res && (res.stage === 'first_appeal_open' ? `b_first_appeal_open_${res.reason === 'replied' ? 'replied' : 'no_reply'}` : `b_${res.stage}`)
  const tone = !res ? '' : res.can_first_appeal || res.can_second_appeal ? 'ok' : res.stage === 'waiting_reply' || res.stage === 'first_appeal_pending' ? 'warn' : 'bad'
  const params = res ? {
    ...Object.fromEntries(Object.entries(res.dates).map(([k, v]) => [k, dateFmt(v)])),
    n: Math.max(0, res.days_left.first_appeal_opens),
    fa_decision_latest: res.dates.fa_decision_latest ? dateFmt(res.dates.fa_decision_latest) : '',
  } : {}

  return (
    <section className="appeal rise" aria-labelledby="ap-h">
      <h2 id="ap-h" className="sec-title">{t('a_title')}</h2>
      <p className="lede">{t('a_sub')}</p>

      <div className="cols">
        <form className="col" onSubmit={e => { e.preventDefault(); run() }}>
          <label className="field"><span>{t('a_filed')}</span>
            <input type="date" required max={iso(new Date())} value={filed} onChange={e => setFiled(e.target.value)} />
          </label>
          <fieldset className="choices"><legend>{t('a_what')}</legend>
            {(['none', 'reply', 'transfer'] as const).map(k => (
              <label key={k} className="choice"><input type="radio" name="what" checked={what === k} onChange={() => setWhat(k)} />
                <span>{t(`a_${k}` as Key)}</span></label>
            ))}
          </fieldset>
          {what === 'reply' && (
            <label className="field"><span>{t('a_reply_on')}</span>
              <input type="date" required max={iso(new Date())} min={filed} value={replied} onChange={e => setReplied(e.target.value)} /></label>
          )}
          <label className="choice"><input type="checkbox" checked={hasFa} onChange={e => setHasFa(e.target.checked)} /><span>{t('a_fa')}</span></label>
          {hasFa && (
            <>
              <label className="field"><span>{t('a_fa_on')}</span>
                <input type="date" required max={iso(new Date())} min={filed} value={faOn} onChange={e => setFaOn(e.target.value)} /></label>
              <label className="choice"><input type="checkbox" checked={decided} onChange={e => setDecided(e.target.checked)} /><span>{t('a_dec')}</span></label>
              {decided && <label className="field"><span>{t('a_dec_on')}</span>
                <input type="date" required max={iso(new Date())} min={faOn} value={decOn} onChange={e => setDecOn(e.target.value)} /></label>}
            </>
          )}
          <button className="btn btn-primary" type="submit">{t('a_check')}</button>
          <div className="examples">
            <div className="small muted">{t('a_examples')}</div>
            <div className="chips">
              {([1, 2, 3, 4] as const).map(n => <button key={n} type="button" className="chip" onClick={() => example(n)}>{t(`a_ex${n}` as Key)}</button>)}
            </div>
          </div>
        </form>

        <div className="col" aria-live="polite">
          {err && <p role="alert" className="note bad">{t('a_err')}</p>}
          {res && (
            <div className={`verdict rise tone-${tone}`} key={res.stage + res.reason + filed}>
              <div className="verdict-badge" aria-hidden>{tone === 'ok' ? '✓' : tone === 'warn' ? '…' : '!'}</div>
              <h2>{t(`s_${res.stage}` as Key)}</h2>
              <p>{fmt(t(stageKey as Key), params)}</p>
              <h3>{t('a_dates')}</h3>
              <ol className="dates">
                {KEYS.filter(k => res.dates[k]).map(k => {
                  const left = res.days_left[k] ?? Math.round((new Date(res.dates[k]).getTime() - Date.now()) / 864e5)
                  return (
                    <li key={k}><span>{t(`d_${k}` as Key)}</span>
                      <strong>{dateFmt(res.dates[k])}</strong>
                      <em className={left < 0 ? 'past' : ''}>{left >= 0 ? `${left} ${t('a_left')}` : `${-left} ${t('a_ago')}`}</em></li>
                  )
                })}
              </ol>
            </div>
          )}
          <p className="small muted disc">{t('a_disc')}</p>
        </div>
      </div>
    </section>
  )
}
