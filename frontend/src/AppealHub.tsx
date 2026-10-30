import { useState } from 'react'
import { AppealCheck } from './Appeal'
import FirstAppeal from './FirstAppeal'
import ReplyReview from './ReplyReview'
import SecondAppeal from './SecondAppeal'
import { useT, type Key } from './i18n'

const TABS = ['check', 'first', 'second', 'reply'] as const
type Tab = (typeof TABS)[number]

export default function AppealHub({ initial = 'check' as Tab }) {
  const { t } = useT()
  const [tab, setTab] = useState<Tab>(initial)
  const [carried, setCarried] = useState<string[]>([])
  return (
    <div className="hub">
      <h1 className="page-title">{t('tools_title')}</h1>
      <p className="lede">{t('tools_sub')}</p>
      <div className="seg" role="tablist" aria-label={t('tools_title')}>
        {TABS.map(k => (
          <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'seg-b on' : 'seg-b'} onClick={() => setTab(k)}>
            {t(`tab_${k}` as Key)}
          </button>
        ))}
      </div>
      <div role="tabpanel" key={tab}>
        {tab === 'check' && <AppealCheck />}
        {tab === 'first' && <FirstAppeal key={carried.join()} initialGrounds={carried} />}
        {tab === 'second' && <SecondAppeal />}
        {tab === 'reply' && <ReplyReview onUse={g => { setCarried(g); setTab('first') }} />}
      </div>
    </div>
  )
}
