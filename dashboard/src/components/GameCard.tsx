import { useState } from 'react'
import type { GameItem } from '../types'

interface Props {
  game: GameItem
}

function formatDate(iso: string): string {
  try {
    return new Intl.DateTimeFormat('en-US', {
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
  const [imgError, setImgError] = useState(false)

  const isPastPromotion = new Date(game.end_date) < new Date()

  return (
    <article className="card">
      <div className="card-image-wrapper">
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
              {isPastPromotion ? 'Was free until' : 'Free until'}:{' '}
              {formatDate(game.end_date)}
            </span>
          </div>
          <span className="card-store">🏪 Epic Games</span>
        </div>
      </div>

      <div className="card-footer">
        <a
          href={game.link}
          className="card-link"
          target="_blank"
          rel="noopener noreferrer"
        >
          View on Epic Games →
        </a>
      </div>
    </article>
  )
}
