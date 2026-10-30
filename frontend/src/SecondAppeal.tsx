import { useEffect, useState } from 'react'
import { appealApi, type AppealOptions, type DraftResult } from './api'
import { useT, type Key } from './i18n'
import { Check, DraftOutput, Field } from './tools'

const iso = (d: Date) => d.toISOString().slice(0, 10)
const DOC_LABEL: Record<string, string> = {}

export default function SecondAppeal() {
  const { t } = useT()
  const [opts, setOpts] = useState<AppealOptions | null>(null)
  const [v, setV] = useState<Record<string, string>>({})
  const [docs, setDocs] = useState<Record<string, boolean>>({})
  const [c, setC] = useState<Record<string, boolean>>({})
  const [res, setRes] = useState<DraftResult | null>(null)
  const set = (k: string) => (x: string) => setV(p => ({ ...p, [k]: x }))
  const flag = (k: string) => (x: boolean) => setC(p => ({ ...p, [k]: x }))
  useEffect(() => { appealApi.options().then(setOpts).catch(() => {}) }, [])
  opts?.docs.forEach(d => { DOC_LABEL[d.code] = d.label })

  const run = async (e: React.FormEvent) => {
    e.preventDefault()
    setRes(await appealApi.second({
      ...v, docs, signed: c.signed, verified_docs: c.verified, legible: c.legible, related: c.related,
      index: c.index, service_proof: c.service, similar_order: c.similar, compensation: c.comp,
      fa_order_on: v.fa_order_on || undefined, first_appeal_on: v.first_appeal_on || undefined,
    }))
  }

  return (
    <section className="rise" aria-labelledby="sa-h">
      <h2 id="sa-h" className="sec-title">{t('tab_second')}</h2>
      <p className="lede">{t('second_src')}</p>
      <div className="cols">
        <form className="col" onSubmit={run}>
          <p className="small muted">{t('s_to')}</p>
          <Field label={t('f_name')} value={v.name ?? ''} onChange={set('name')} />
          <Field label={t('f_address')} value={v.address ?? ''} onChange={set('address')} rows={2} />
          <div className="pair">
            <Field label={t('f_phone')} value={v.phone ?? ''} onChange={set('phone')} />
            <Field label={t('f_email')} value={v.email ?? ''} onChange={set('email')} type="email" />
          </div>
          <Field label={t('f_authority')} value={v.authority ?? ''} onChange={set('authority')} />
          <Field label={t('f_cpio_to')} value={v.cpio_to ?? ''} onChange={set('cpio_to')} />
          <Field label={t('f_cpio_reply')} value={v.cpio_reply ?? ''} onChange={set('cpio_reply')} />
          <Field label={t('f_faa')} value={v.faa ?? ''} onChange={set('faa')} />
          <div className="pair">
            <Field label={t('f_reg')} value={v.reg_no ?? ''} onChange={set('reg_no')} />
            <Field label={t('f_filed')} value={v.filed_on ?? ''} onChange={set('filed_on')} type="date" max={iso(new Date())} />
          </div>
          <Field label={t('f_sought')} value={v.sought ?? ''} onChange={set('sought')} rows={2} />
          <div className="pair">
            <Field label={t('f_fa_on')} value={v.first_appeal_on ?? ''} onChange={set('first_appeal_on')} type="date" max={iso(new Date())} />
            <Field label={t('f_fa_order_on')} value={v.fa_order_on ?? ''} onChange={set('fa_order_on')} type="date" max={iso(new Date())} />
          </div>
          <Field label={t('f_fa_order_no')} value={v.fa_order_no ?? ''} onChange={set('fa_order_no')} />
          <Field label={t('f_facts')} value={v.facts ?? ''} onChange={set('facts')} rows={4} />
          <Field label={t('f_grounds')} value={v.grounds ?? ''} onChange={set('grounds')} rows={4} />
          <Field label={t('f_prayer')} value={v.prayer ?? ''} onChange={set('prayer')} rows={3} />
          <Check label={t('f_comp')} checked={!!c.comp} onChange={flag('comp')} />
          {c.comp && <Field label={t('f_comp_g')} value={v.compensation_grounds ?? ''} onChange={set('compensation_grounds')} rows={3} />}
          <Field label={t('f_cond')} value={v.condonation ?? ''} onChange={set('condonation')} rows={3} />
          <Field label={t('f_other')} value={v.other ?? ''} onChange={set('other')} rows={2} />

          <fieldset className="choices"><legend>{t('docs_h')}</legend>
            {opts?.docs.map(d => (
              <Check key={d.code} label={d.label + (d.mandatory ? ' *' : '')} checked={!!docs[d.code]}
                onChange={x => setDocs(p => ({ ...p, [d.code]: x }))} />
            ))}
          </fieldset>
          <fieldset className="choices"><legend>{t('checks_h')}</legend>
            {(['signed', 'verified', 'legible', 'related', 'index', 'service', 'similar'] as const).map(k => (
              <Check key={k} label={t(`c_${k}` as Key)} checked={!!c[k]} onChange={flag(k)} />
            ))}
          </fieldset>
          <button className="btn btn-primary" type="submit">{t('draft_btn')}</button>
        </form>
        <div className="col">{res && <DraftOutput text={res.text} name="second-appeal.txt" ready={res.ready} issues={res.issues} />}</div>
      </div>
    </section>
  )
}
