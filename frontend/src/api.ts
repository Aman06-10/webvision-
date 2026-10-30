const BASE = '/api'

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(BASE + path, init)
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    throw new ApiError(r.status, body.detail ?? r.statusText)
  }
  return r.json()
}

const json = (method: string, body: unknown, headers: Record<string, string> = {}): RequestInit => ({
  method, headers: { 'Content-Type': 'application/json', ...headers }, body: JSON.stringify(body),
})

export type Validation = { length: number; max: number; too_long: boolean; invalid_chars: string[]; invalid_positions: number[]; ok: boolean }
export type AuthorityResult = { key: string; authority: string; level: string; portal: string; confidence: number; reason: string; source: string; authority_hi?: string; portal_hi?: string; candidates: { key: string; name: string; name_hi?: string; score: number }[] }
export type AppEvent = { kind: string; detail: string; at: string }
export type Application = {
  id: number; email: string; draft: string; state: string; rti_number: string | null
  authority_key: string | null; authority_confirmed: number; created_at: string
  events?: AppEvent[]
}
export type Translation = { original: string; translated: string; engine: string; quality?: 'verified' | 'beta' }
export type Lang = { name: string; quality: 'verified' | 'beta' }
export type Answer = { answer: string; sources: { id: string; title: string }[]; retrieval: string; answered_by: string }

export const api = {
  health: () => call<{ llm: boolean; stt: boolean; tts: boolean; bhashini: boolean }>('/health'),
  languages: () => call<Record<string, Lang>>('/languages'),
  ask: (question: string, lang: string) => call<Answer>('/rag/ask', json('POST', { question, lang })),
  speak: async (text: string, lang: string) => {
    const r = await fetch(BASE + '/voice/speak', json('POST', { text, lang }))
    if (!r.ok) throw new ApiError(r.status, 'tts')
    return r.blob()
  },
  create: (email: string) => call<Application>('/applications', json('POST', { email })),
  list: (email: string) => call<Application[]>(`/applications?email=${encodeURIComponent(email)}`),
  get: (id: number) => call<Application>(`/applications/${id}`),
  saveDraft: (id: number, draft: string, source_lang: string, original_text: string) =>
    call<Validation>(`/applications/${id}/draft`, json('PUT', { draft, source_lang, original_text })),
  sanitize: (draft: string) => call<{ draft: string }>('/draft/sanitize', json('POST', { draft })),
  refine: (draft: string) => call<{ draft: string }>('/draft/refine', json('POST', { draft })),
  translate: (text: string, src: string, target: string) =>
    call<Translation>('/voice/translate', json('POST', { text, src, target })),
  transcribe: (wav: Blob, src: string, target: string) => {
    const f = new FormData(); f.append('audio', wav, 'speech.wav'); f.append('src', src); f.append('target', target)
    return call<Translation>('/voice/transcribe', { method: 'POST', body: f })
  },
  findAuthority: (text: string) => call<AuthorityResult>('/authority/find', json('POST', { text })),
  authorities: () => call<{ key: string; name: string; name_hi?: string; level: string }[]>('/authority/list'),
  confirmAuthority: (id: number, authority_key: string) =>
    call(`/applications/${id}/authority`, json('POST', { authority_key })),
  pay: (id: number, key: string, scenario: string) =>
    call(`/applications/${id}/pay`, json('POST', { scenario }, { 'Idempotency-Key': key })),
}

export type AppealResult = {
  stage: string; can_first_appeal: boolean; can_second_appeal: boolean; reason: string
  dates: Record<string, string>; days_left: Record<string, number>
}
export type AppealInput = {
  filed: string; replied?: string; first_appeal?: string; fa_decided?: string; transferred_physically?: boolean
}
export const checkAppeal = (b: AppealInput) => call<AppealResult>('/appeal/check', json('POST', b))
