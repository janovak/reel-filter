/**
 * SearchPage Component
 * Main search interface with filter panel and movie results grid with pagination
 */

import { useState, useEffect } from 'react'
import { SearchResponse } from '../types/api.types'
import { useFilters } from '../hooks/useFilters'
import FilterPanel from '../components/FilterPanel'
import MovieCard from '../components/MovieCard'
import apiClient from '../services/api'

const SearchPage = () => {
  const { filters, updateFilter, resetFilters } = useFilters()
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasSearched, setHasSearched] = useState(false)

  /**
   * Perform search with current filters
   */
  const performSearch = async (pageNum: number = 1) => {
    try {
      setLoading(true)
      setError(null)

      // Build query params from filters
      const params: Record<string, string | number> = {
        page: pageNum,
        per_page: filters.per_page || 30,
      }

      // Add search query
      if (filters.q) {
        params.q = filters.q
      }

      // Add content thresholds (only if not "any")
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
      })

      setSearchResults(response.data)
      setHasSearched(true)

      // Update page in filters to keep in sync
      if (pageNum !== filters.page) {
        updateFilter('page', pageNum)
      }
    } catch (err) {
      console.error('Search error:', err)
      setError('Failed to search movies. Please try again.')
      setHasSearched(true)
    } finally {
      setLoading(false)
    }
  }

  /**
   * Handle search input change
   */
  const handleSearchChange = (query: string) => {
    updateFilter('q', query)
  }

  /**
   * Trigger search on filters change
   */
  useEffect(() => {
    if (hasSearched) {
      performSearch(1) // Reset to page 1 when filters change
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.q, filters.sex_max, filters.violence_max, filters.language_max])

  /**
   * Handle pagination
   */
  const handlePageChange = (newPage: number) => {
    performSearch(newPage)
  }

  /**
   * Handle reset
   */
  const handleReset = () => {
    resetFilters()
    setSearchResults(null)
    setHasSearched(false)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Reel-Filter</h1>
          <p className="text-lg text-gray-600">
            Discover movies that match your content preferences
          </p>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <input
            type="text"
            placeholder="Search by movie title..."
            value={filters.q || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full px-4 py-3 text-lg border-2 border-gray-300 rounded-lg focus:outline-none focus:border-brand-primary transition"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filter Panel (Sidebar) */}
          <div className="lg:col-span-1">
            <FilterPanel
              filters={filters}
              onFilterChange={updateFilter}
              onReset={handleReset}
            />
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            {/* Initial state - no search yet */}
            {!hasSearched && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <p className="text-gray-600 text-lg mb-4">
                  Start by searching for a movie or adjusting your content preferences
                </p>
                <button
                  onClick={() => {
                    setHasSearched(true)
                    performSearch(1)
                  }}
                  className="px-6 py-3 bg-brand-primary text-white font-semibold rounded-lg hover:bg-blue-600 transition"
                >
                  Browse All Movies
                </button>
              </div>
            )}

            {/* Loading state */}
            {loading && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <div className="inline-block">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-primary"></div>
                </div>
                <p className="text-gray-600 mt-4">Searching movies...</p>
              </div>
            )}

            {/* Error state */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <p className="text-red-700 font-semibold">{error}</p>
                <button
                  onClick={() => performSearch(searchResults?.pagination.page || 1)}
                  className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
                >
                  Try Again
                </button>
              </div>
            )}

            {/* Results - No movies found */}
            {hasSearched && !loading && !error && searchResults && searchResults.movies.length === 0 && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <p className="text-gray-600 text-lg">
                  No movies found matching your criteria.
                </p>
                <p className="text-gray-500 mt-2">Try adjusting your filters or search query.</p>
              </div>
            )}

            {/* Results - Movies Grid */}
            {hasSearched && !loading && !error && searchResults && searchResults.movies.length > 0 && (
              <>
                {/* Results Info */}
                <div className="mb-6 text-gray-600">
                  <p className="text-sm">
                    Showing {(searchResults.pagination.page - 1) * searchResults.pagination.per_page + 1} to{' '}
                    {Math.min(searchResults.pagination.page * searchResults.pagination.per_page, searchResults.pagination.total)} of{' '}
                    <strong>{searchResults.pagination.total}</strong> movies
                  </p>
                </div>

                {/* Movie Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
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
                  <div className="flex items-center justify-center gap-2 bg-white rounded-lg shadow-md p-6">
                    {/* Previous Button */}
                    <button
                      onClick={() => handlePageChange(searchResults.pagination.page - 1)}
                      disabled={!searchResults.pagination.has_prev}
                      className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-semibold hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                    >
                      ← Previous
                    </button>

                    {/* Page Number Display and Input */}
                    <div className="flex items-center gap-2">
                      <span className="text-gray-700">
                        Page{' '}
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
                          className="w-16 px-2 py-1 border border-gray-300 rounded text-center focus:outline-none focus:ring-2 focus:ring-brand-primary"
                        />
                        {' of '}
                        <strong>{searchResults.pagination.total_pages}</strong>
                      </span>
                    </div>

                    {/* Next Button */}
                    <button
                      onClick={() => handlePageChange(searchResults.pagination.page + 1)}
                      disabled={!searchResults.pagination.has_next}
                      className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-semibold hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition"
                    >
                      Next →
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default SearchPage
