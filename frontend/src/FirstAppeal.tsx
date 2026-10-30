import { useEffect, useState } from 'react'
import { appealApi, type AppealOptions, type DraftResult } from './api'
import { useT, type Key } from './i18n'
import { Check, DraftOutput, Field } from './tools'

const iso = (d: Date) => d.toISOString().slice(0, 10)

export default function FirstAppeal({ seed, initialGrounds }: { seed?: Record<string, string>; initialGrounds?: string[] }) {
  const { t } = useT()
  const [opts, setOpts] = useState<AppealOptions | null>(null)
  const [v, setV] = useState<Record<string, string>>({ relief: 'provide', ...seed })
  const [grounds, setGrounds] = useState<string[]>(initialGrounds ?? [])
  const [res, setRes] = useState<DraftResult | null>(null)
  const set = (k: string) => (x: string) => setV(p => ({ ...p, [k]: x }))
  useEffect(() => { appealApi.options().then(setOpts).catch(() => {}) }, [])

  const toggle = (g: string) => setGrounds(p => (p.includes(g) ? p.filter(x => x !== g) : [...p, g]))
  const run = async (e: React.FormEvent) => {
    e.preventDefault()
    setRes(await appealApi.first({ ...v, grounds, replied_on: v.replied_on || undefined }))
  }

  return (
    <section className="rise" aria-labelledby="fa-h">
      <h2 id="fa-h" className="sec-title">{t('tab_first')}</h2>
      <p className="lede">{t('first_note')}</p>
      <div className="cols">
        <form className="col" onSubmit={run}>
          <Field label={t('f_name')} value={v.name ?? ''} onChange={set('name')} />
          <Field label={t('f_address')} value={v.address ?? ''} onChange={set('address')} rows={2} />
          <div className="pair">
            <Field label={t('f_phone')} value={v.phone ?? ''} onChange={set('phone')} />
            <Field label={t('f_email')} value={v.email ?? ''} onChange={set('email')} type="email" />
          </div>
          <Field label={t('f_authority')} value={v.authority ?? ''} onChange={set('authority')} />
          <div className="pair">
            <Field label={t('f_reg')} value={v.reg_no ?? ''} onChange={set('reg_no')} />
            <Field label={t('f_filed')} value={v.filed_on ?? ''} onChange={set('filed_on')} type="date" max={iso(new Date())} />
          </div>
          <Field label={t('f_cpio')} value={v.cpio ?? ''} onChange={set('cpio')} />
          <Field label={t('f_reply_on')} value={v.replied_on ?? ''} onChange={set('replied_on')} type="date" max={iso(new Date())} />
          <Field label={t('f_reply_sum')} value={v.reply_summary ?? ''} onChange={set('reply_summary')} rows={2} />
          <Field label={t('f_sought')} value={v.sought ?? ''} onChange={set('sought')} rows={3} />
          <fieldset className="choices"><legend>{t('g_title')}</legend>
            {opts && Object.keys(opts.grounds).map(g => (
              <Check key={g} label={t(`g_${g}` as Key)} checked={grounds.includes(g)} onChange={() => toggle(g)} />
            ))}
          </fieldset>
          <Field label={t('f_extra')} value={v.extra ?? ''} onChange={set('extra')} rows={3} />
          <label className="field"><span>{t('f_relief')}</span>
            <select value={v.relief} onChange={e => set('relief')(e.target.value)}>
              {opts && Object.keys(opts.relief).map(k => <option key={k} value={k}>{t(`rl_${k}` as Key)}</option>)}
            </select>
          </label>
          <button className="btn btn-primary" type="submit">{t('draft_btn')}</button>
        </form>
        <div className="col">{res && <DraftOutput text={res.text} name="first-appeal.txt" ready={res.ready} issues={res.issues} />}</div>
      </div>
    </section>
  )
}

