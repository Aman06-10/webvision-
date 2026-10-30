// Record the mic and convert to 16 kHz mono WAV, which is what speech services expect.
export async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
  const rec = new MediaRecorder(stream)
  const chunks: Blob[] = []
  rec.ondataavailable = e => chunks.push(e.data)
  rec.start()
  return {
    stop: () => new Promise<Blob>(resolve => {
      rec.onstop = async () => {
        stream.getTracks().forEach(t => t.stop())
        resolve(await toWav16k(new Blob(chunks)))
      }
      rec.stop()
    }),
  }
}

async function toWav16k(blob: Blob): Promise<Blob> {
  const ctx = new AudioContext()
  const decoded = await ctx.decodeAudioData(await blob.arrayBuffer())
  await ctx.close()
  const frames = Math.ceil(decoded.duration * 16000)
  const off = new OfflineAudioContext(1, frames, 16000)
  const src = off.createBufferSource()
  src.buffer = decoded
  src.connect(off.destination)
  src.start()
  const pcm = (await off.startRendering()).getChannelData(0)

  const buf = new ArrayBuffer(44 + pcm.length * 2)
  const v = new DataView(buf)
  const str = (o: number, s: string) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)))
  str(0, 'RIFF'); v.setUint32(4, 36 + pcm.length * 2, true); str(8, 'WAVEfmt ')
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true)
  v.setUint32(24, 16000, true); v.setUint32(28, 32000, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true)
  str(36, 'data'); v.setUint32(40, pcm.length * 2, true)
  pcm.forEach((s, i) => v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, s)) * 0x7fff, true))
  return new Blob([buf], { type: 'audio/wav' })
}

// Fallback: browser speech recognition (Chrome sends audio to Google).
const BCP47: Record<string, string> = {
  hi: 'hi-IN', en: 'en-IN', bn: 'bn-IN', ta: 'ta-IN', te: 'te-IN', mr: 'mr-IN', gu: 'gu-IN',
  kn: 'kn-IN', ml: 'ml-IN', pa: 'pa-IN', or: 'or-IN', as: 'as-IN', ur: 'ur-IN',
}
export const speechSupported = () => 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window

export function startBrowserSpeech(lang: string, onText: (t: string) => void, onEnd: () => void) {
  const Ctor = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  const r = new Ctor()
  r.lang = BCP47[lang] ?? 'en-IN'
  r.interimResults = true
  r.continuous = true
  r.onresult = (e: any) => onText([...e.results].map((x: any) => x[0].transcript).join(' '))
  r.onend = onEnd
  r.onerror = onEnd
  r.start()
  return { stop: () => r.stop() }
}

// Read text aloud: NVIDIA voice for Hindi and English, browser voice for the rest.
let current: HTMLAudioElement | null = null
export async function speak(text: string, lang: string, speakFn: (t: string, l: string) => Promise<Blob>) {
  current?.pause()
  if (lang === 'hi' || lang === 'en') {
    try {
      const url = URL.createObjectURL(await speakFn(text, lang))
      current = new Audio(url)
      current.onended = () => URL.revokeObjectURL(url)
      await current.play()
      return
    } catch { /* fall through to browser voice */ }
  }
  if ('speechSynthesis' in window) {
    const u = new SpeechSynthesisUtterance(text)
    u.lang = BCP47[lang] ?? 'en-IN'
    speechSynthesis.cancel(); speechSynthesis.speak(u)
  }
}
