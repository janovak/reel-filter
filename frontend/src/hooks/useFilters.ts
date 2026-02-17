/**
 * useFilters hook for session storage
 */
import { useState, useEffect } from 'react'
import { SearchFilters } from '../types/api.types'

const STORAGE_KEY = 'reel-filter-search-filters'

// Default filter values
const getDefaultFilters = (): SearchFilters => ({
  q: '',
  genres: [],
  year_min: undefined,
  year_max: undefined,
  mpaa_ratings: [],
  imdb_min: 0,
  rt_min: 0,
  metacritic_min: 0,
  awards_min: undefined,
  sex_max: null, // null = "any" (no limit)
  violence_max: null,
  language_max: null,
  page: 1,
  per_page: 30,
})

/**
 * Custom hook for managing search filters with session storage persistence
 */
export function useFilters() {
  const [filters, setFilters] = useState<SearchFilters>(() => {
    // Initialize from sessionStorage on mount
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      if (stored) {
        return JSON.parse(stored)
      }
    } catch (error) {
      console.error('Failed to load filters from session storage:', error)
    }
    return getDefaultFilters()
  })

  // Persist to sessionStorage whenever filters change
  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(filters))
    } catch (error) {
      console.error('Failed to save filters to session storage:', error)
    }
  }, [filters])

  /**
   * Update specific filter fields
   */
  const updateFilter = <K extends keyof SearchFilters>(
    key: K,
    value: SearchFilters[K]
  ) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      page: key === 'page' ? (value as number) : 1, // Reset to page 1 when filters change (except page itself)
    }))
  }

  /**
   * Reset all filters to default values
   */
  const resetFilters = () => {
    setFilters(getDefaultFilters())
    sessionStorage.removeItem(STORAGE_KEY)
  }

  /**
   * Check if any content filters are active (not "any")
   */
  const hasContentFilters = () => {
    return (
      filters.sex_max !== null ||
      filters.violence_max !== null ||
      filters.language_max !== null
    )
  }

  return {
    filters,
    setFilters,
    updateFilter,
    resetFilters,
    hasContentFilters,
  }
}
