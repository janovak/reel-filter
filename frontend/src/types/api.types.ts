/**
 * TypeScript types from API schema
 */

// Movie entity
export interface Movie {
  id: string
  title: string
  year: number
  runtime?: number
  genre: string[]
  mpaa_rating?: string
  plot?: string
  director?: string
  cast: string[]
  poster_url?: string
  imdb_rating?: number
  rt_rating?: number
  metacritic_rating?: number
  awards_summary?: string
  awards_count: number
  nominations_count: number
  awards_metadata?: Record<string, unknown>
  omdb_id: string
  source: string
  created_at: string
  updated_at: string
  content_score?: ContentScore
}

// Content score entity
export interface ContentScore {
  id: string
  movie_id: string
  sex_nudity: number
  violence_gore: number
  language_profanity: number
  source: string
  source_available: boolean
  scraped_at: string
  updated_at: string
  match_confidence?: number
  manually_reviewed: boolean
}

// Search filters
export interface SearchFilters {
  q?: string // Title search
  genres?: string[]
  year_min?: number
  year_max?: number
  mpaa_ratings?: string[]
  imdb_min?: number
  rt_min?: number
  metacritic_min?: number
  awards_min?: number
  sex_max?: number | null // null = "any"
  violence_max?: number | null
  language_max?: number | null
  page?: number
  per_page?: number
}

// Pagination metadata
export interface PaginationInfo {
  page: number
  per_page: number
  total: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

// Search response
export interface SearchResponse {
  movies: Movie[]
  pagination: PaginationInfo
}

// Health check response
export interface HealthResponse {
  status: string
  database: string
  last_refresh?: string
}

// Error response
export interface ErrorResponse {
  error: string
  message: string
  details?: unknown
}

// MPAA ratings enum
export const MPAA_RATINGS = ['G', 'PG', 'PG-13', 'R', 'NC-17', 'Not Rated'] as const
export type MpaaRating = typeof MPAA_RATINGS[number]

// Genre enum (common genres)
export const GENRES = [
  'Action', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime',
  'Documentary', 'Drama', 'Family', 'Fantasy', 'History', 'Horror',
  'Music', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Sport',
  'Thriller', 'War', 'Western'
] as const
export type Genre = typeof GENRES[number]
