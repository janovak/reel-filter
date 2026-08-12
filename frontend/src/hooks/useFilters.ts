/**
 * useFilters hook for session storage
 *
 * Owns the React-lifecycle side of the Filter Set: reading and writing
 * sessionStorage, and resetting to page 1 when a filter changes. The Filter
 * Set domain module (src/domain/filterSet.ts) owns the defaults and the
 * merge used to restore a Filter Set from storage — this hook just calls it.
 */
import { useState, useEffect } from 'react'
import { SearchFilters } from '../types/api.types'
import { getDefaultFilterSet, restoreFilterSet } from '../domain/filterSet'

const STORAGE_KEY = 'reel-filter-search-filters'

/**
 * Custom hook for managing search filters with session storage persistence
 */
export function useFilters() {
  const [filters, setFilters] = useState<SearchFilters>(() => {
    // Initialize from sessionStorage on mount
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      if (stored) {
        return restoreFilterSet(JSON.parse(stored))
      }
    } catch (error) {
      console.error('Failed to load filters from session storage:', error)
    }
    return getDefaultFilterSet()
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
    setFilters(getDefaultFilterSet())
    sessionStorage.removeItem(STORAGE_KEY)
  }

  return {
    filters,
    setFilters,
    updateFilter,
    resetFilters,
  }
}
