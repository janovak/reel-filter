/**
 * SearchPage Component
 * Main search interface with SearchBar, FilterPanel (sidebar/drawer), MovieCard grid, and pagination.
 * Passes all filter parameters (content + traditional + quality) to API.
 * Mobile responsive with filter drawer overlay.
 */

import { useState, useEffect, useCallback } from 'react'
import { SearchResponse } from '../types/api.types'
import { useFilters } from '../hooks/useFilters'
import SearchBar from '../components/SearchBar'
import FilterPanel from '../components/FilterPanel'
import MovieCard from '../components/MovieCard'
import apiClient from '../services/api'

const SearchPage = () => {
  const { filters, updateFilter, resetFilters } = useFilters()
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)
  const [mobileFilterOpen, setMobileFilterOpen] = useState(false)

  /**
   * Perform search with current filters
   */
  const performSearch = useCallback(async (pageNum: number = 1) => {
    try {
      setLoading(true)
      setError(null)

      // Build query params from ALL filters
      const params: Record<string, string | number | string[]> = {
        page: pageNum,
        per_page: filters.per_page || 30,
      }

      // Text search
      if (filters.q && filters.q.trim()) {
        params.q = filters.q.trim()
      }

      // Genre filter
      if (filters.genres && filters.genres.length > 0) {
        params.genres = filters.genres
      }

      // Year range
      if (filters.year_min) params.year_min = filters.year_min
      if (filters.year_max) params.year_max = filters.year_max

      // MPAA ratings
      if (filters.mpaa_ratings && filters.mpaa_ratings.length > 0) {
        params.mpaa_ratings = filters.mpaa_ratings
      }

      // Quality ratings
      if (filters.imdb_min && filters.imdb_min > 0) params.imdb_min = filters.imdb_min
      if (filters.rt_min && filters.rt_min > 0) params.rt_min = filters.rt_min
      if (filters.metacritic_min && filters.metacritic_min > 0) params.metacritic_min = filters.metacritic_min

      // Awards
      if (filters.awards_min && filters.awards_min > 0) params.awards_min = filters.awards_min

      // Content thresholds (only if not "any")
      if (filters.sex_max !== null && filters.sex_max !== undefined) {
        params.sex_max = filters.sex_max
      }
      if (filters.violence_max !== null && filters.violence_max !== undefined) {
        params.violence_max = filters.violence_max
      }
      if (filters.language_max !== null && filters.language_max !== undefined) {
        params.language_max = filters.language_max
      }

      // Call API
      const response = await apiClient.get<SearchResponse>('/movies/search', {
        params,
        paramsSerializer: {
          indexes: null, // Send arrays as genres=Action&genres=Drama
        },
      })

      setSearchResults(response.data)
      setHasSearched(true)

      if (pageNum !== filters.page) {
        updateFilter('page', pageNum)
      }
    } catch (err) {
      console.error('Search error:', err)
      setError('Failed to search movies. Please check your connection and try again.')
      setHasSearched(true)
    } finally {
      setLoading(false)
    }
  }, [filters, updateFilter])

  /**
   * Auto-search when filters change (debounced by useFilters/SearchBar)
   */
  useEffect(() => {
    if (hasSearched) {
      performSearch(1)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    filters.q,
    filters.sex_max, filters.violence_max, filters.language_max,
    filters.genres?.join(','),
    filters.year_min, filters.year_max,
    filters.mpaa_ratings?.join(','),
    filters.imdb_min, filters.rt_min, filters.metacritic_min,
    filters.awards_min,
  ])

  /**
   * Handle pagination
   */
  const handlePageChange = (newPage: number) => {
    performSearch(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  /**
   * Handle reset
   */
  const handleReset = () => {
    resetFilters()
    setSearchResults(null)
    setHasSearched(false)
    setMobileFilterOpen(false)
  }

  /**
   * Count active filters (for mobile badge)
   */
  const activeFilterCount = [
    filters.sex_max !== null && filters.sex_max !== undefined,
    filters.violence_max !== null && filters.violence_max !== undefined,
    filters.language_max !== null && filters.language_max !== undefined,
    filters.genres && filters.genres.length > 0,
    !!filters.year_min,
    !!filters.year_max,
    filters.mpaa_ratings && filters.mpaa_ratings.length > 0,
    filters.imdb_min && filters.imdb_min > 0,
    filters.rt_min && filters.rt_min > 0,
    filters.metacritic_min && filters.metacritic_min > 0,
    filters.awards_min && filters.awards_min > 0,
  ].filter(Boolean).length

  /**
   * Get filter relaxation suggestions based on active filters
   */
  const getRelaxSuggestions = (): string[] => {
    const suggestions: string[] = []
    if (filters.q) suggestions.push('Try a different search term or clear the search')
    if (filters.sex_max !== null || filters.violence_max !== null || filters.language_max !== null) {
      suggestions.push('Increase content thresholds or set to "No limit"')
    }
    if (filters.genres && filters.genres.length > 0) suggestions.push('Remove some genre filters')
    if (filters.imdb_min && filters.imdb_min > 0) suggestions.push('Lower the minimum IMDb rating')
    if (filters.year_min || filters.year_max) suggestions.push('Widen the year range')
    if (suggestions.length === 0) suggestions.push('Try different search criteria')
    return suggestions
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-30">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-gray-900">
                🎬 Reel-Filter
              </h1>
              <p className="text-sm text-gray-500 hidden sm:block">
                Discover movies that match your content preferences
              </p>
            </div>
          </div>

          {/* Search Bar */}
          <div className="flex gap-2 items-stretch">
            <div className="flex-1">
              <SearchBar
                value={filters.q || ''}
                onChange={(q) => updateFilter('q', q)}
                onSearch={() => {
                  setHasSearched(true)
                  performSearch(1)
                }}
              />
            </div>

            {/* Mobile Filter Toggle */}
            <button
              onClick={() => setMobileFilterOpen(true)}
              className="lg:hidden flex items-center gap-1.5 px-4 py-2 bg-white border-2 border-gray-300
                         rounded-xl text-gray-700 font-medium hover:bg-gray-50 transition min-h-[44px]
                         relative"
              aria-label="Open filters"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              <span className="text-sm">Filters</span>
              {activeFilterCount > 0 && (
                <span className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-brand-primary text-white text-xs font-bold rounded-full flex items-center justify-center">
                  {activeFilterCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* Desktop Filter Sidebar */}
          <aside className="hidden lg:block w-72 xl:w-80 flex-shrink-0">
            <div className="sticky top-[140px]">
              <FilterPanel
                filters={filters}
                onFilterChange={updateFilter}
                onReset={handleReset}
              />
            </div>
          </aside>

          {/* Results Area */}
          <div className="flex-1 min-w-0">
            {/* Initial state - no search yet */}
            {!hasSearched && (
              <div className="bg-white rounded-lg shadow-md p-8 md:p-12 text-center">
                <div className="max-w-md mx-auto">
                  <div className="text-5xl mb-4">🎬</div>
                  <h2 className="text-xl font-bold text-gray-800 mb-2">
                    Find the right movie for you
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Search by title, filter by genre, ratings, and set your content comfort levels
                  </p>
                  <button
                    onClick={() => {
                      setHasSearched(true)
                      performSearch(1)
                    }}
                    className="px-6 py-3 bg-brand-primary text-white font-semibold rounded-lg
                               hover:bg-blue-600 active:bg-blue-700 transition min-h-[44px]"
                  >
                    Browse All Movies
                  </button>
                </div>
              </div>
            )}

            {/* Loading state */}
            {loading && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <div className="inline-block">
                  <div className="animate-spin rounded-full h-10 w-10 border-4 border-gray-200 border-t-brand-primary"></div>
                </div>
                <p className="text-gray-500 mt-4 text-sm">Searching movies...</p>
              </div>
            )}

            {/* Error state */}
            {error && !loading && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <div className="text-3xl mb-2">⚠️</div>
                <p className="text-red-700 font-semibold mb-1">{error}</p>
                <button
                  onClick={() => performSearch(searchResults?.pagination.page || 1)}
                  className="mt-3 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700
                             transition text-sm font-medium min-h-[44px]"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* No results */}
            {hasSearched && !loading && !error && searchResults && searchResults.movies.length === 0 && (
              <div className="bg-white rounded-lg shadow-md p-8 md:p-12 text-center">
                <div className="text-5xl mb-4">🔍</div>
                <h3 className="text-lg font-bold text-gray-800 mb-2">
                  No movies found
                </h3>
                <p className="text-gray-500 mb-4">Try adjusting your filters:</p>
                <ul className="text-sm text-gray-600 space-y-1 mb-6">
                  {getRelaxSuggestions().map((suggestion, i) => (
                    <li key={i} className="flex items-center justify-center gap-2">
                      <span className="text-brand-primary">•</span> {suggestion}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={handleReset}
                  className="px-5 py-2.5 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300
                             transition text-sm font-medium min-h-[44px]"
                >
                  Clear All Filters
                </button>
              </div>
            )}

            {/* Results Grid */}
            {hasSearched && !loading && !error && searchResults && searchResults.movies.length > 0 && (
              <>
                {/* Results count */}
                <div className="mb-4 flex items-center justify-between">
                  <p className="text-sm text-gray-500">
                    Showing{' '}
                    <span className="font-semibold text-gray-700">
                      {(searchResults.pagination.page - 1) * searchResults.pagination.per_page + 1}
                      –
                      {Math.min(
                        searchResults.pagination.page * searchResults.pagination.per_page,
                        searchResults.pagination.total
                      )}
                    </span>
                    {' '}of{' '}
                    <span className="font-semibold text-gray-700">{searchResults.pagination.total}</span>
                    {' '}movies
                  </p>
                </div>

                {/* Movie Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4 md:gap-5 mb-8">
                  {searchResults.movies.map((movie) => (
                    <MovieCard
                      key={movie.id}
                      movie={movie}
                      sexThreshold={filters.sex_max}
                      violenceThreshold={filters.violence_max}
                      languageThreshold={filters.language_max}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {searchResults.pagination.total_pages > 1 && (
                  <div className="flex items-center justify-center gap-2 bg-white rounded-lg shadow-md p-4">
                    <button
                      onClick={() => handlePageChange(searchResults.pagination.page - 1)}
                      disabled={!searchResults.pagination.has_prev}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-gray-700 text-sm font-medium
                                 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition min-h-[44px]"
                    >
                      ← Prev
                    </button>

                    <div className="flex items-center gap-1.5 text-sm text-gray-600">
                      <span>Page</span>
                      <input
                        type="number"
                        min="1"
                        max={searchResults.pagination.total_pages}
                        value={searchResults.pagination.page}
                        onChange={(e) => {
                          const page = parseInt(e.target.value, 10)
                          if (page >= 1 && page <= searchResults.pagination.total_pages) {
                            handlePageChange(page)
                          }
                        }}
                        className="w-14 px-2 py-1 border border-gray-300 rounded text-center text-sm
                                   focus:outline-none focus:ring-2 focus:ring-brand-primary min-h-[36px]"
                      />
                      <span>of <strong>{searchResults.pagination.total_pages}</strong></span>
                    </div>

                    <button
                      onClick={() => handlePageChange(searchResults.pagination.page + 1)}
                      disabled={!searchResults.pagination.has_next}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-gray-700 text-sm font-medium
                                 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition min-h-[44px]"
                    >
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </main>

      {/* Mobile Filter Drawer Overlay */}
      {mobileFilterOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setMobileFilterOpen(false)}
          />
          {/* Drawer */}
          <div className="absolute inset-y-0 right-0 w-full max-w-sm bg-gray-50 shadow-2xl overflow-y-auto">
            {/* Drawer Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between z-10">
              <h2 className="text-lg font-bold text-gray-800">Filters</h2>
              <button
                onClick={() => setMobileFilterOpen(false)}
                className="p-2 text-gray-500 hover:text-gray-700 min-w-[44px] min-h-[44px] flex items-center justify-center"
                aria-label="Close filters"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            {/* Drawer Content */}
            <div className="p-4">
              <FilterPanel
                filters={filters}
                onFilterChange={updateFilter}
                onReset={handleReset}
                onApply={() => {
                  setMobileFilterOpen(false)
                  if (!hasSearched) {
                    setHasSearched(true)
                  }
                  performSearch(1)
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12 py-6">
        <div className="container mx-auto px-4 text-center text-sm text-gray-500">
          <p>
            Reel-Filter • Content data from Kids-in-Mind • Movie data from OMDb API
          </p>
          <p className="mt-1">
            <a href="/docs" target="_blank" rel="noopener noreferrer" className="text-brand-primary hover:underline">
              API Documentation
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}

export default SearchPage
