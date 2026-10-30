import { useT, type Key } from './i18n'

const TONE: Record<string, string> = {
  SUBMITTED: 'ok', PAYMENT_PENDING: 'warn', PAYMENT_FAILED: 'bad', DRAFT: 'plain',
}

export default function Stamp({ state }: { state: string }) {
  const { t } = useT()
  return <span className={`pill pill-${TONE[state] ?? 'plain'}`}><i />{t(`st_${state}` as Key)}</span>
}
