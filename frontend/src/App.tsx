import { useEffect, useState } from 'react'
import { api, type Application } from './api'
import AppealHub from './AppealHub'
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
  const [menu, setMenu] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const sysDark = () => window.matchMedia('(prefers-color-scheme: dark)').matches
  const [theme, setTheme] = useState<'light' | 'dark'>((read('theme') as 'light' | 'dark') || (sysDark() ? 'dark' : 'light'))
  const [scale, setScale] = useState(Number(read('scale')) || 100)
  const [health, setHealth] = useState<{ llm: boolean; stt: boolean; tts: boolean } | null>(null)

  const t = (k: Key) => strings[lang][k]
  const go = (v: typeof view) => { setView(v); setMenu(false); window.scrollTo(0, 0) }
  useEffect(() => { document.documentElement.lang = lang; write('lang', lang) }, [lang])
  useEffect(() => { api.health().then(setHealth).catch(() => setHealth(null)) }, [])
  useEffect(() => { if (email) write('email', email) }, [email])
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    document.querySelector('meta[name=theme-color]')?.setAttribute('content', theme === 'dark' ? '#0b1b30' : '#16365f')
  }, [theme])
  useEffect(() => {
    // follow the system until the visitor picks a theme
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const f = () => { if (!read('theme')) setTheme(mq.matches ? 'dark' : 'light') }
    mq.addEventListener('change', f)
    return () => mq.removeEventListener('change', f)
  }, [])
  useEffect(() => { document.documentElement.style.fontSize = `${17 * scale / 100}px`; write('scale', String(scale)) }, [scale])
  useEffect(() => {
    const f = () => setScrolled(window.scrollY > 6)
    f(); window.addEventListener('scroll', f, { passive: true })
    return () => window.removeEventListener('scroll', f)
  }, [])

  return (
    <LangCtx.Provider value={{ lang, t }}>
      <a className="skip" href="#main">Skip to content</a>
      <header className={scrolled ? 'top scrolled' : 'top'}>
        <div className="wrap top-row">
          <button className="brand" onClick={() => go('home')}><span className="brand-mark" aria-hidden>RTI</span>{t('brand')}</button>
          <button className="menu-btn" aria-expanded={menu} aria-controls="main-nav" onClick={() => setMenu(m => !m)}>{t('menu')}</button>
          <nav aria-label="Main" id="main-nav" className={menu ? 'open' : ''}>
            <button className={view === 'home' ? 'tab on' : 'tab'} onClick={() => go('home')}>{t('nav_home')}</button>
            <button className={view === 'new' ? 'tab on' : 'tab'} onClick={() => { setResume(null); go('new') }}>{t('nav_new')}</button>
            <button className={view === 'mine' ? 'tab on' : 'tab'} onClick={() => go('mine')} disabled={!email}>{t('nav_mine')}</button>
            <button className={view === 'appeal' ? 'tab on' : 'tab'} onClick={() => go('appeal')}>{t('nav_appeal')}</button>
            <button className={view === 'help' ? 'tab on' : 'tab'} onClick={() => go('help')}>{t('nav_help')}</button>
          </nav>
          <div className="fontsw" role="group" aria-label="Text size">
            <button aria-label={t('font_dec')} onClick={() => setScale(s => Math.max(85, s - 10))}>A-</button>
            <button aria-label={t('font_reset')} onClick={() => setScale(100)}>A</button>
            <button aria-label={t('font_inc')} onClick={() => setScale(s => Math.min(135, s + 10))}>A+</button>
          </div>
          <button className="theme-btn" onClick={() => setTheme(x => { const n = x === 'dark' ? 'light' : 'dark'; write('theme', n); return n })}
            aria-label={theme === 'dark' ? t('theme_light') : t('theme_dark')} title={theme === 'dark' ? t('theme_light') : t('theme_dark')}>
            {theme === 'dark'
              ? <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
              : <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>}
          </button>
          <div className="langsw" role="group" aria-label="Interface language">
            <button aria-pressed={lang === 'en'} onClick={() => setLang('en')}>EN</button>
            <button aria-pressed={lang === 'hi'} onClick={() => setLang('hi')} lang="hi">हिं</button>
          </div>
        </div>
      </header>
      <main id="main" className="wrap">
        {view === 'home' ? <Home go={v => { setResume(null); go(v) }} />
          : view === 'help' ? <Help />
          : view === 'appeal' ? <AppealHub />
          : view === 'new'
            ? <RequestFlow key={resume?.id ?? 'new'} email={email} setEmail={setEmail} resume={resume} />
            : <Dashboard email={email} onOpen={a => { setResume(a); go('new') }} onNew={() => { setResume(null); go('new') }} onAppeal={() => go('appeal')} />}
      </main>
      <footer className="wrap foot">
        <p>{t('concept')}</p>
        <p className="small">{t('official_portals')}: <a href="https://rtionline.gov.in" target="_blank" rel="noreferrer">rtionline.gov.in</a> · <a href="https://cic.gov.in" target="_blank" rel="noreferrer">cic.gov.in</a></p>
        {health && (
          <p className="mono small">
            {t('health_llm')}: {health.llm ? t('on') : t('off')} · {t('health_bh')}: {health.stt && health.tts ? t('on') : t('off')}
          </p>
        )}
      </footer>
    </LangCtx.Provider>
  )
}
