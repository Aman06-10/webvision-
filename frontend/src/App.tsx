import { useEffect, useState } from 'react'
import { api, type Application } from './api'
import Appeal from './Appeal'
import Dashboard from './Dashboard'
import Home from './Home'
import Help from './Help'
import RequestFlow from './RequestFlow'
import { LangCtx, strings, type Key, type Lang } from './i18n'

const read = (k: string) => { try { return localStorage.getItem(k) } catch { return null } }
const write = (k: string, v: string) => { try { localStorage.setItem(k, v) } catch { /* ignore */ } }

export default function App() {
  const [lang, setLang] = useState<Lang>((read('lang') as Lang) || 'en')
  const [view, setView] = useState<'home' | 'new' | 'mine' | 'help' | 'appeal'>('home')
  const [email, setEmail] = useState(read('email') ?? '')
  const [resume, setResume] = useState<Application | null>(null)
  const [health, setHealth] = useState<{ llm: boolean; stt: boolean; tts: boolean; bhashini: boolean } | null>(null)

  const t = (k: Key) => strings[lang][k]
  useEffect(() => { document.documentElement.lang = lang; write('lang', lang) }, [lang])
  useEffect(() => { api.health().then(setHealth).catch(() => setHealth(null)) }, [])
  useEffect(() => { if (email) write('email', email) }, [email])

  return (
    <LangCtx.Provider value={{ lang, t }}>
      <a className="skip" href="#main">Skip to content</a>
      <header className="top">
        <div className="wrap top-row">
          <button className="brand" onClick={() => setView('home')}><span className="brand-mark" aria-hidden>RTI</span>{t('brand')}</button>
          <nav aria-label="Main">
            <button className={view === 'home' ? 'tab on' : 'tab'} onClick={() => setView('home')}>{t('nav_home')}</button>
            <button className={view === 'new' ? 'tab on' : 'tab'} onClick={() => { setResume(null); setView('new') }}>{t('nav_new')}</button>
            <button className={view === 'mine' ? 'tab on' : 'tab'} onClick={() => setView('mine')} disabled={!email}>{t('nav_mine')}</button>
            <button className={view === 'appeal' ? 'tab on' : 'tab'} onClick={() => setView('appeal')}>{t('nav_appeal')}</button>
            <button className={view === 'help' ? 'tab on' : 'tab'} onClick={() => setView('help')}>{t('nav_help')}</button>
          </nav>
          <div className="langsw" role="group" aria-label="Interface language">
            <button aria-pressed={lang === 'en'} onClick={() => setLang('en')}>EN</button>
            <button aria-pressed={lang === 'hi'} onClick={() => setLang('hi')} lang="hi">हिं</button>
          </div>
        </div>
      </header>
      <main id="main" className="wrap">
        {view === 'home' ? <Home go={v => { setResume(null); setView(v) }} />
          : view === 'help' ? <Help />
          : view === 'appeal' ? <Appeal />
          : view === 'new'
            ? <RequestFlow key={resume?.id ?? 'new'} email={email} setEmail={setEmail} resume={resume} />
            : <Dashboard email={email} onOpen={a => { setResume(a); setView('new') }} />}
      </main>
      <footer className="wrap foot">
        <p>{t('concept')}</p>
        {health && (
          <p className="mono small">
            {t('health_llm')}: {health.llm ? t('on') : t('off')} · {t('health_bh')}: {health.stt && health.tts ? t('on') : t('off')}
          </p>
        )}
      </footer>
    </LangCtx.Provider>
  )
}
