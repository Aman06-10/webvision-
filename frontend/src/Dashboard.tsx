import { useEffect, useState } from 'react'
import { api, type Application } from './api'
import Stamp from './Stamp'
import { useT } from './i18n'

type Props = { email: string; onOpen: (a: Application) => void; onNew: () => void; onAppeal: () => void }

export default function Dashboard({ email, onOpen, onNew, onAppeal }: Props) {
  const { t } = useT()
  const [rows, setRows] = useState<Application[] | null>(null)
  useEffect(() => { api.list(email).then(setRows).catch(() => setRows([])) }, [email])

  return (
    <section aria-labelledby="mine-h" className="rise">
      <h1 id="mine-h" className="page-title">{t('mine_h')}</h1>
      {rows === null && <div className="skeleton"><span /><span /><span /></div>}
      {rows && rows.length === 0 && (
        <div className="empty">
          <svg width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="M6 3h9l4 4v14H6z" /><path d="M14 3v5h5M9 13h6M9 17h4" />
          </svg>
          <h2>{t('db_empty_h')}</h2><p className="muted">{t('db_empty_p')}</p>
          <button className="btn btn-primary" onClick={onNew}>{t('db_new')}</button>
        </div>
      )}
      <ul className="req-list">
        {rows?.map((a, i) => (
          <li key={a.id} style={{ ['--i' as string]: i }}>
            <div className="req-main">
              <div className="mono small muted">{a.rti_number ?? `#${String(a.id).padStart(4, '0')}`} · {a.created_at.slice(0, 10)}</div>
              <div className="clip">{a.draft || '—'}</div>
            </div>
            <Stamp state={a.state} />
            <div className="req-actions">
              <button className="btn btn-sm btn-quiet" onClick={() => onOpen(a)}>{t('open')}</button>
              {a.state === 'SUBMITTED' && <button className="btn btn-sm btn-quiet" onClick={onAppeal}>{t('db_appeal')}</button>}
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
