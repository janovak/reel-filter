/**
 * FilterPanel Component
 * Controls for filtering movies by content thresholds and other criteria
 */

import { useState } from 'react'
import { SearchFilters } from '../types/api.types'

interface FilterPanelProps {
  filters: SearchFilters
  onFilterChange: <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => void
  onReset: () => void
}

const FilterPanel = ({ filters, onFilterChange, onReset }: FilterPanelProps) => {
  const [expanded, setExpanded] = useState(true)

  // Content threshold controls - "any" is represented by null
  const handleContentSliderChange = (
    key: 'sex_max' | 'violence_max' | 'language_max',
    value: string
  ) => {
    if (value === 'any') {
      onFilterChange(key, null)
    } else {
      onFilterChange(key, parseInt(value, 10))
    }
  }

  const handleAnyCheckboxChange = (
    key: 'sex_max' | 'violence_max' | 'language_max',
    checked: boolean
  ) => {
    if (checked) {
      onFilterChange(key, null) // "any" = null
    }
  }

  // Get current value for display (handle null = "any")
  const isAnySelected = (threshold: number | null | undefined): boolean => {
    return threshold === null || threshold === undefined
  }

  const ContentThresholdControl = ({
    label,
    filterKey,
    value,
  }: {
    label: string
    filterKey: 'sex_max' | 'violence_max' | 'language_max'
    value: number | null | undefined
  }) => (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm font-semibold text-brand-primary">
          {isAnySelected(value) ? 'Any' : value}
        </span>
      </div>

      <div className="flex items-center gap-4">
        <input
          type="range"
          min="0"
          max="10"
          step="1"
          value={isAnySelected(value) ? '0' : (value ?? 0)}
          onChange={(e) => handleContentSliderChange(filterKey, e.target.value)}
          disabled={isAnySelected(value)}
          className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        />
      </div>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={isAnySelected(value)}
          onChange={(e) => handleAnyCheckboxChange(filterKey, e.target.checked)}
          className="w-4 h-4 rounded border-gray-300 cursor-pointer"
        />
        <span className="text-gray-600">Show all</span>
      </label>
    </div>
  )

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div
        className="flex items-center justify-between cursor-pointer mb-4"
        onClick={() => setExpanded(!expanded)}
      >
        <h2 className="text-xl font-bold text-gray-800">Filters</h2>
        <button className="text-gray-500 hover:text-gray-700">
          {expanded ? '−' : '+'}
        </button>
      </div>

      {expanded && (
        <div className="space-y-6">
          {/* Content Thresholds */}
          <div className="border-t pt-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Content Thresholds</h3>
            <div className="space-y-6">
              <ContentThresholdControl
                label="Sex & Nudity"
                filterKey="sex_max"
                value={filters.sex_max}
              />
              <ContentThresholdControl
                label="Violence & Gore"
                filterKey="violence_max"
                value={filters.violence_max}
              />
              <ContentThresholdControl
                label="Language & Profanity"
                filterKey="language_max"
                value={filters.language_max}
              />
            </div>
          </div>

          {/* Reset Button */}
          <div className="flex gap-2 pt-4 border-t">
            <button
              onClick={onReset}
              className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold rounded-lg transition"
            >
              Reset All
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default FilterPanel
