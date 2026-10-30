import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'

const reduced = () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

// Adds class "in" once the element scrolls into view.
export function useInView<T extends HTMLElement>(threshold = 0.18) {
  const ref = useRef<T>(null)
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el || seen) return
    if (reduced()) { setSeen(true); return }
    // IntersectionObserver is the main path; a scroll check backs it up so content can never stay hidden.
    const visible = () => { const r = el.getBoundingClientRect(); return r.top < window.innerHeight * 0.92 && r.bottom > 0 }
    let io: IntersectionObserver | undefined
    const done = () => { io?.disconnect(); window.removeEventListener('scroll', on); window.removeEventListener('resize', on) }
    const on = () => { if (visible()) { setSeen(true); done() } }
    if (visible()) { setSeen(true); return }
    if ('IntersectionObserver' in window) {
      io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setSeen(true); done() } }, { threshold })
      io.observe(el)
    }
    window.addEventListener('scroll', on, { passive: true })
    window.addEventListener('resize', on)
    return done
  }, [seen, threshold])
  return [ref, seen] as const
}

export function Reveal({ children, delay = 0, as: Tag = 'div', className = '' }: { children: ReactNode; delay?: number; as?: 'div' | 'section' | 'li'; className?: string }) {
  const [ref, seen] = useInView<HTMLDivElement>()
  const T = Tag as 'div'
  return <T ref={ref} className={`reveal ${seen ? 'in' : ''} ${className}`} style={{ ['--d' as string]: `${delay}ms` }}>{children}</T>
}

// Counts every number inside a string up from zero when it scrolls into view ("3.85 lakh", "24 to 48").
export function CountUp({ text, ms = 1400 }: { text: string; ms?: number }) {
  const [ref, seen] = useInView<HTMLSpanElement>(0.4)
  const [p, setP] = useState(0)
  useEffect(() => {
    if (!seen) return
    if (reduced()) { setP(1); return }
    const t0 = performance.now()
    // setInterval rather than requestAnimationFrame so the count still finishes if the tab is throttled.
    const h = window.setInterval(() => {
      const k = Math.max(0, Math.min(1, (performance.now() - t0) / ms))
      setP(1 - Math.pow(1 - k, 3))
      if (k >= 1) window.clearInterval(h)
    }, 40)
    return () => window.clearInterval(h)
  }, [seen, ms])
  const out = useMemo(() => text.replace(/\d[\d,]*(\.\d+)?/g, m => {
    const dec = (m.split('.')[1] ?? '').length
    const v = parseFloat(m.replace(/,/g, '')) * p
    return v.toLocaleString('en-IN', { minimumFractionDigits: dec, maximumFractionDigits: dec })
  }), [text, p])
  return <span ref={ref} aria-label={text}>{seen ? out : text.replace(/\d[\d,]*(\.\d+)?/g, '0')}</span>
}

// A short burst of paper bits when a request is submitted.
export function Confetti() {
  const bits = useMemo(() => Array.from({ length: 34 }, (_, i) => {
    const a = (i / 34) * Math.PI * 2 + Math.random() * 0.4
    const d = 90 + Math.random() * 120
    return { i, x: Math.cos(a) * d, y: Math.sin(a) * d - 40, r: Math.random() * 540 - 270, c: ['navy', 'saffron', 'green'][i % 3], w: 6 + Math.random() * 6, h: 3 + Math.random() * 4, del: Math.random() * 120 }
  }), [])
  return (
    <div className="confetti" aria-hidden>
      {bits.map(b => (
        <i key={b.i} className={`cf cf-${b.c}`} style={{ ['--x' as string]: `${b.x}px`, ['--y' as string]: `${b.y}px`, ['--r' as string]: `${b.r}deg`, width: b.w, height: b.h, animationDelay: `${b.del}ms` }} />
      ))}
    </div>
  )
}
