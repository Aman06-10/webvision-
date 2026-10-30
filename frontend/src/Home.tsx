import { useEffect, useState } from 'react'
import { useT, type Key } from './i18n'

type Props = { go: (v: 'new' | 'appeal' | 'help') => void }

function Typed({ text }: { text: string }) {
  const [n, setN] = useState(0)
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { setN(text.length); return }
    setN(0)
    const h = setInterval(() => setN(i => (i >= text.length ? (clearInterval(h), i) : i + 1)), 28)
    return () => clearInterval(h)
  }, [text])
  return <>{text.slice(0, n)}<span className="caret" aria-hidden>|</span></>
}

export default function Home({ go }: Props) {
  const { t } = useT()
  const facts = [1, 2, 3, 4, 5, 6] as const
  const pairs = [1, 2, 3, 4, 5] as const
  return (
    <div className="home">
      <section className="hero rise">
        <div className="hero-text">
          <span className="eyebrow">{t('h_eyebrow')}</span>
          <h1>{t('h_title')}</h1>
          <p className="hero-sub">{t('h_sub')}</p>
          <div className="hero-cta">
            <button className="btn btn-primary btn-big" onClick={() => go('new')}>{t('h_cta')} <span aria-hidden>→</span></button>
            <button className="btn btn-big" onClick={() => go('appeal')}>{t('h_cta2')}</button>
          </div>
          <p className="small muted">{t('h_trust')}</p>
        </div>
        <div className="hero-demo" aria-hidden>
          <div className="demo-card">
            <div className="demo-label">{t('h_demo_in')}</div>
            <div className="demo-hi" lang="hi">{t('h_demo_hi')}</div>
          </div>
          <div className="demo-arrow"><i /></div>
          <div className="demo-card demo-out">
            <div className="demo-label">{t('h_demo_out')}</div>
            <div className="demo-en" lang="en"><Typed text={t('h_demo_en')} /></div>
          </div>
        </div>
      </section>

      <section className="know" aria-labelledby="k-h">
        <h2 id="k-h">{t('k_title')}</h2>
        <p className="small muted">{t('k_src')}</p>
        <ul className="facts">
          {facts.map(n => (
            <li key={n}><span className="fact-n" aria-hidden>{n}</span>
              <div><strong>{t(`k${n}h` as Key)}</strong><p>{t(`k${n}` as Key)}</p></div></li>
          ))}
        </ul>
      </section>

      <section className="problems" aria-labelledby="p-h">
        <h2 id="p-h">{t('p_title')}</h2>
        <div className="pgrid" role="table">
          <div className="phead" role="row"><span role="columnheader">{t('p_now')}</span><span role="columnheader">{t('p_new')}</span></div>
          {pairs.map(n => (
            <div className="prow" role="row" key={n}>
              <p className="p-now" role="cell">{t(`p${n}a` as Key)}</p>
              <p className="p-new" role="cell">{t(`p${n}b` as Key)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="how" aria-labelledby="w-h">
        <h2 id="w-h">{t('w_title')}</h2>
        <ol className="how-steps">
          {([1, 2, 3] as const).map(n => (
            <li key={n}><span className="how-n">{n}</span><h3>{t(`w${n}h` as Key)}</h3><p>{t(`w${n}` as Key)}</p></li>
          ))}
        </ol>
      </section>

      <section className="band">
        <div><h2>{t('band_t')}</h2><p>{t('band_p')}</p></div>
        <div className="band-cta">
          <button className="btn btn-saffron btn-big" onClick={() => go('new')}>{t('h_cta')} <span aria-hidden>→</span></button>
          <button className="btn btn-ghost btn-big" onClick={() => go('help')}>{t('nav_help')}</button>
        </div>
      </section>
    </div>
  )
}
