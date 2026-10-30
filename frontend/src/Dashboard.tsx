import { useEffect, useState } from 'react'
import { api, type Application } from './api'
import Stamp from './Stamp'
import { useT } from './i18n'

export default function Dashboard({ email, onOpen }: { email: string; onOpen: (a: Application) => void }) {
  const { t } = useT()
  const [rows, setRows] = useState<Application[] | null>(null)
  useEffect(() => { api.list(email).then(setRows).catch(() => setRows([])) }, [email])

  return (
    <section aria-labelledby="mine-h">
      <h1 id="mine-h" className="page-title">{t('mine_h')}</h1>
      {rows && rows.length === 0 && <p className="muted">{t('none')}</p>}
      <ul className="ledger-list">
        {rows?.map(a => (
          <li key={a.id}>
            <div>
              <div className="mono small">{a.rti_number ?? `#${String(a.id).padStart(4, '0')}`}</div>
              <div className="clip">{a.draft || '—'}</div>
            </div>
            <Stamp state={a.state} />
            <button className="btn btn-quiet" onClick={() => onOpen(a)}>{t('open')}</button>
          </li>
        ))}
      </ul>
    </section>
  )
}
