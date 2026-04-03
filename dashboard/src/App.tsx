import { useState, useEffect, useCallback } from 'react'
import type { GameItem, GamesHistoryResponse, SortField, SortDirection } from './types'
import GameCard from './components/GameCard'
import Pagination from './components/Pagination'

const PAGE_SIZE = 12

export default function App() {
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
              <h1>Free Games History</h1>
              <p>All previously tracked free game promotions</p>
            </div>
          </div>
          {!loading && !error && (
            <div className="header-stats">
              <span className="stat-badge">{total} games tracked</span>
            </div>
          )}
        </div>
      </header>

      <main className="main">
        <div className="toolbar">
          <div className="search-wrapper">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="search-input"
              placeholder="Search by title or description…"
              value={search}
              onChange={e => handleSearch(e.target.value)}
              aria-label="Search games"
            />
            {search && (
              <button
                className="clear-btn"
                onClick={() => handleSearch('')}
                aria-label="Clear search"
              >
                ✕
              </button>
            )}
          </div>
          <div className="sort-controls">
            <span className="sort-label">Sort by:</span>
            <SortButton field="end_date" label="Date" />
            <SortButton field="title" label="Title" />
          </div>
        </div>

        {loading && (
          <div className="state-container">
            <div className="spinner" />
            <p>Loading games…</p>
          </div>
        )}

        {error && (
          <div className="state-container error">
            <span className="state-icon">⚠️</span>
            <p>{error}</p>
            <button className="retry-btn" onClick={fetchGames}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && filtered.length === 0 && (
          <div className="state-container">
            <span className="state-icon">🕹️</span>
            <p>
              {search
                ? `No games match "${search}"`
                : 'No games in history yet.'}
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
        <p>
          Free Games Notifier &mdash; Game history dashboard &middot; Data from{' '}
          <a
            href="https://www.epicgames.com/store/free-games"
            target="_blank"
            rel="noopener noreferrer"
          >
            Epic Games
          </a>
        </p>
      </footer>
    </div>
  )
}
