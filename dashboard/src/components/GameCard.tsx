import { useState } from 'react'
import type { GameItem } from '../types'
import { useTranslation } from '../i18n'
import type { Locale } from '../i18n/translations'
import { localeBcp47 } from '../i18n/translations'

const STORE_META: Record<string, { label: string; icon: string }> = {
  epic:  { label: 'Epic Games', icon: '🏪' },
  steam: { label: 'Steam',      icon: '🎮' },
}

function getStoreMeta(store: string) {
  return STORE_META[store] ?? { label: store, icon: '🏪' }
}

interface Props {
  game: GameItem
}

function formatDate(iso: string, locale: Locale): string {
  try {
    return new Intl.DateTimeFormat(localeBcp47[locale], {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZoneName: 'short',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}

export default function GameCard({ game }: Props) {
  const { t, locale } = useTranslation()
  const [imgError, setImgError] = useState(false)

  const isPastPromotion = new Date(game.end_date) < new Date()
  const storeMeta = getStoreMeta(game.store)
  const isDlc = game.game_type === 'dlc'

  return (
    <article className="card">
      <div className="card-image-wrapper">
        {isDlc && (
          <span className="card-dlc-badge" aria-label={t.dlcBadge}>
            {t.dlcBadge}
          </span>
        )}
        {game.thumbnail && !imgError ? (
          <img
            className="card-image"
            src={game.thumbnail}
            alt={game.title}
            loading="lazy"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="card-image-fallback" aria-hidden="true">
            🎮
          </div>
        )}
      </div>

      <div className="card-body">
        <h2 className="card-title" title={game.title}>
          {game.title}
        </h2>

        {game.description && (
          <p className="card-description" title={game.description}>
            {game.description}
          </p>
        )}

        <div className="card-meta">
          <div className="card-date">
            <span className="card-date-icon">📅</span>
            <span>
              {isPastPromotion ? t.wasFreeUntil : t.freeUntil}:{' '}
              {formatDate(game.end_date, locale)}
            </span>
          </div>
          <span className="card-store">{storeMeta.icon} {storeMeta.label}</span>
        </div>
      </div>

      <div className="card-footer">
        <a
          href={game.link}
          className="card-link"
          target="_blank"
          rel="noopener noreferrer"
        >
          {t.viewOnStore(storeMeta.label)}
        </a>
      </div>
    </article>
  )
}
