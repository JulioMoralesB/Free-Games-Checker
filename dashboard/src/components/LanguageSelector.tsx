import { useTranslation } from '../i18n'
import type { Locale } from '../i18n/translations'

const LOCALE_LABELS: Record<Locale, string> = {
  en: '🇺🇸 EN',
  es: '🇪🇸 ES',
}

export default function LanguageSelector() {
  const { locale, setLocale, t } = useTranslation()

  return (
    <div className="lang-selector" aria-label={t.languageLabel}>
      {(Object.keys(LOCALE_LABELS) as Locale[]).map((lang) => (
        <button
          key={lang}
          className={`lang-btn${locale === lang ? ' active' : ''}`}
          onClick={() => setLocale(lang)}
          aria-pressed={locale === lang}
          title={t.languageLabel}
        >
          {LOCALE_LABELS[lang]}
        </button>
      ))}
    </div>
  )
}
