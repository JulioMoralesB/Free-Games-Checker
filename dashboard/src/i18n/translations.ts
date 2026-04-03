export type Locale = 'en' | 'es'

export interface Translations {
  // Header
  headerTitle: string
  headerSubtitle: string
  gamesTracked: (count: number) => string

  // Toolbar
  searchPlaceholder: string
  searchAriaLabel: string
  clearSearchAriaLabel: string
  sortBy: string
  sortByDate: string
  sortByTitle: string

  // Loading / error / empty states
  loadingGames: string
  errorRetry: string
  noGamesMatch: (query: string) => string
  noGamesYet: string

  // GameCard
  wasFreeUntil: string
  freeUntil: string
  epicGamesStore: string
  viewOnEpicGames: string

  // Pagination
  previousPage: string
  nextPage: string
  pageN: (n: number) => string

  // Footer
  footerText: string
  footerEpicGamesLink: string

  // Language selector
  languageLabel: string
}

const en: Translations = {
  // Header
  headerTitle: 'Free Games History',
  headerSubtitle: 'All previously tracked free game promotions',
  gamesTracked: (count) => `${count} games tracked`,

  // Toolbar
  searchPlaceholder: 'Search by title or description…',
  searchAriaLabel: 'Search games',
  clearSearchAriaLabel: 'Clear search',
  sortBy: 'Sort by:',
  sortByDate: 'Date',
  sortByTitle: 'Title',

  // Loading / error / empty states
  loadingGames: 'Loading games…',
  errorRetry: 'Retry',
  noGamesMatch: (query) => `No games match "${query}"`,
  noGamesYet: 'No games in history yet.',

  // GameCard
  wasFreeUntil: 'Was free until',
  freeUntil: 'Free until',
  epicGamesStore: '🏪 Epic Games',
  viewOnEpicGames: 'View on Epic Games →',

  // Pagination
  previousPage: 'Previous page',
  nextPage: 'Next page',
  pageN: (n) => `Page ${n}`,

  // Footer
  footerText: 'Free Games Notifier — Game history dashboard · Data from',
  footerEpicGamesLink: 'Epic Games',

  // Language selector
  languageLabel: 'Language',
}

const es: Translations = {
  // Header
  headerTitle: 'Historial de Juegos Gratis',
  headerSubtitle: 'Todas las promociones de juegos gratis registradas',
  gamesTracked: (count) => `${count} juegos registrados`,

  // Toolbar
  searchPlaceholder: 'Buscar por título o descripción…',
  searchAriaLabel: 'Buscar juegos',
  clearSearchAriaLabel: 'Limpiar búsqueda',
  sortBy: 'Ordenar por:',
  sortByDate: 'Fecha',
  sortByTitle: 'Título',

  // Loading / error / empty states
  loadingGames: 'Cargando juegos…',
  errorRetry: 'Reintentar',
  noGamesMatch: (query) => `No se encontraron juegos para "${query}"`,
  noGamesYet: 'Aún no hay juegos en el historial.',

  // GameCard
  wasFreeUntil: 'Estuvo gratis hasta',
  freeUntil: 'Gratis hasta',
  epicGamesStore: '🏪 Epic Games',
  viewOnEpicGames: 'Ver en Epic Games →',

  // Pagination
  previousPage: 'Página anterior',
  nextPage: 'Página siguiente',
  pageN: (n) => `Página ${n}`,

  // Footer
  footerText: 'Free Games Notifier — Panel de historial de juegos · Datos de',
  footerEpicGamesLink: 'Epic Games',

  // Language selector
  languageLabel: 'Idioma',
}

export const translations: Record<Locale, Translations> = { en, es }

/**
 * Maps our short `Locale` codes to full BCP 47 language tags accepted by
 * `Intl.DateTimeFormat` (e.g. 'en' → 'en-US', 'es' → 'es-ES').
 * Add an entry here when registering a new locale.
 */
export const localeBcp47: Record<Locale, string> = {
  en: 'en-US',
  es: 'es-ES',
}

/**
 * Detect the preferred locale from the browser's language settings.
 * Falls back to 'en' if no supported locale is found.
 *
 * To add a new language:
 *   1. Add a new key to the `Locale` union type above.
 *   2. Create a translation object implementing `Translations`.
 *   3. Register it in the `translations` map.
 */
export function detectLocale(): Locale {
  const supported = Object.keys(translations) as Locale[]
  for (const lang of navigator.languages ?? [navigator.language]) {
    const base = lang.split('-')[0].toLowerCase()
    if (supported.includes(base as Locale)) return base as Locale
  }
  return 'en'
}
