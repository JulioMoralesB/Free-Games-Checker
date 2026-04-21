import { useState, useEffect, useCallback } from 'react'
import type { GameItem, GamesHistoryResponse, SortField, SortDirection } from './types'
import GameCard from './components/GameCard'
import Pagination from './components/Pagination'
import LanguageSelector from './components/LanguageSelector'
import { useTranslation } from './i18n'

const PAGE_SIZE = 12

export default function App() {
  const { t } = useTranslation()
  const [games, setGames] = useState<GameItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState<SortField>('end_date')
  const [sortDir, setSortDir] = useState<SortDirection>('desc')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const offset = (page - 1) * PAGE_SIZE

  const fetchGames = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`/games/history?limit=${PAGE_SIZE}&offset=${offset}`)
      if (!res.ok) throw new Error(`Server responded with ${res.status}`)
      const data: GamesHistoryResponse = await res.json()
      setGames(data.games)
      setTotal(data.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch games')
    } finally {
      setLoading(false)
    }
  }, [offset])

  useEffect(() => {
    fetchGames()
  }, [fetchGames])

  // Reset to page 1 when search changes
  const handleSearch = (value: string) => {
    setSearch(value)
    setPage(1)
  }

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(field)
      setSortDir('desc')
    }
  }

  // Client-side filter + sort on the current page
  const filtered = games
    .filter(g => {
      if (!search) return true
      const q = search.toLowerCase()
      return (
        g.title.toLowerCase().includes(q) ||
        g.description.toLowerCase().includes(q)
      )
    })
    .sort((a, b) => {
      const mul = sortDir === 'asc' ? 1 : -1
      if (sortBy === 'title') return a.title.localeCompare(b.title) * mul
      return (
        (new Date(a.end_date).getTime() - new Date(b.end_date).getTime()) * mul
      )
    })

  const totalPages = Math.ceil(total / PAGE_SIZE)

  const SortButton = ({
    field,
    label,
  }: {
    field: SortField
    label: string
  }) => (
    <button
      className={`sort-btn${sortBy === field ? ' active' : ''}`}
      onClick={() => handleSort(field)}
      aria-pressed={sortBy === field}
    >
      {label}
      {sortBy === field && (
        <span className="sort-icon">{sortDir === 'asc' ? ' ↑' : ' ↓'}</span>
      )}
    </button>
  )

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="header-title">
            <span className="header-icon">🎮</span>
            <div>
              <h1>{t.headerTitle}</h1>
              <p>{t.headerSubtitle}</p>
            </div>
          </div>
          <div className="header-actions">
            {!loading && !error && (
              <div className="header-stats">
                <span className="stat-badge">{t.gamesTracked(total)}</span>
              </div>
            )}
            <LanguageSelector />
          </div>
        </div>
      </header>

      <main className="main">
        <div className="toolbar">
          <div className="search-wrapper">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="search-input"
              placeholder={t.searchPlaceholder}
              value={search}
              onChange={e => handleSearch(e.target.value)}
              aria-label={t.searchAriaLabel}
            />
            {search && (
              <button
                className="clear-btn"
                onClick={() => handleSearch('')}
                aria-label={t.clearSearchAriaLabel}
              >
                ✕
              </button>
            )}
          </div>
          <div className="sort-controls">
            <span className="sort-label">{t.sortBy}</span>
            <SortButton field="end_date" label={t.sortByDate} />
            <SortButton field="title" label={t.sortByTitle} />
          </div>
        </div>

        {loading && (
          <div className="state-container">
            <div className="spinner" />
            <p>{t.loadingGames}</p>
          </div>
        )}

        {error && (
          <div className="state-container error">
            <span className="state-icon">⚠️</span>
            <p>{error}</p>
            <button className="retry-btn" onClick={fetchGames}>
              {t.errorRetry}
            </button>
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="state-container">
            <span className="state-icon">🕹️</span>
            <p>
              {search
                ? t.noGamesMatch(search)
                : t.noGamesYet}
            </p>
          </div>
        )}

        {!loading && !error && filtered.length > 0 && (
          <div className="grid">
            {filtered.map((game, i) => (
              <GameCard key={game.link || `${game.title}-${i}`} game={game} />
            ))}
          </div>
        )}

        {!loading && !error && totalPages > 1 && (
          <Pagination
            page={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        )}
      </main>

      <footer className="footer">
        <p>{t.footerText}</p>
      </footer>
    </div>
  )
}
