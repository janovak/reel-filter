/**
 * FilterPanel Component
 * Full filter controls: content thresholds, genre, year, MPAA, quality ratings, awards
 * Mobile responsive with collapsible sections
 */

import { useState, useEffect, useRef } from 'react'
import { SearchFilters, MPAA_RATINGS, GENRES } from '../types/api.types'
import apiClient from '../services/api'

/**
 * Reusable range slider that tracks drag locally and only commits on release.
 */
const RangeSlider = ({
  label, min, max, step, value, displayValue, onCommit, color, accent, ticks, disabled,
}: {
  label: string; min: number; max: number; step: number; value: number
  displayValue: (v: number) => string; onCommit: (v: number) => void
  color: string; accent: string; ticks?: string[]; disabled?: boolean
}) => {
  const [local, setLocal] = useState(value)
  const dragging = useRef(false)

  useEffect(() => {
    if (!dragging.current) setLocal(value)
  }, [value])

  const shown = dragging.current ? local : value

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className={`text-sm font-bold ${color}`}>{displayValue(shown)}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={shown}
        onPointerDown={() => { dragging.current = true }}
        onInput={(e) => {
          const v = parseFloat((e.target as HTMLInputElement).value)
          setLocal(v)
        }}
        onPointerUp={(e) => {
          dragging.current = false
          onCommit(parseFloat((e.target as HTMLInputElement).value))
        }}
        onChange={() => {}} // Controlled input — commit handled by onPointerUp
        disabled={disabled}
        className={`w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer ${accent}
                    ${disabled ? 'opacity-40 cursor-not-allowed' : ''}`}
      />
      {ticks && (
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          {ticks.map((t) => <span key={t}>{t}</span>)}
        </div>
      )}
    </div>
  )
}

interface FilterPanelProps {
  filters: SearchFilters
  onFilterChange: <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => void
  onReset: () => void
  onApply?: () => void
}

const FilterPanel = ({ filters, onFilterChange, onReset, onApply }: FilterPanelProps) => {
  const [contentExpanded, setContentExpanded] = useState(true)
  const [traditionalExpanded, setTraditionalExpanded] = useState(true)
  const [qualityExpanded, setQualityExpanded] = useState(false)
  const [availableGenres, setAvailableGenres] = useState<string[]>([...GENRES])

  // Fetch available genres from API
  useEffect(() => {
    const fetchGenres = async () => {
      try {
        const response = await apiClient.get<{ genres: string[] }>('/genres')
        if (response.data.genres && response.data.genres.length > 0) {
          setAvailableGenres(response.data.genres)
        }
      } catch {
        // Fall back to static list
      }
    }
    fetchGenres()
  }, [])

  // Content threshold controls
  const handleContentSliderChange = (
    key: 'sex_max' | 'violence_max' | 'language_max',
    value: string
  ) => {
    onFilterChange(key, parseInt(value, 10))
  }

  const handleAnyCheckboxChange = (
    key: 'sex_max' | 'violence_max' | 'language_max',
    checked: boolean
  ) => {
    if (checked) {
      onFilterChange(key, null)
    } else {
      onFilterChange(key, 5) // Default to 5 when enabling
    }
  }

  const isAnySelected = (threshold: number | null | undefined): boolean => {
    return threshold === null || threshold === undefined
  }

  // Genre toggle
  const handleGenreToggle = (genre: string) => {
    const current = filters.genres || []
    const updated = current.includes(genre)
      ? current.filter((g) => g !== genre)
      : [...current, genre]
    onFilterChange('genres', updated.length > 0 ? updated : undefined)
  }

  // MPAA rating toggle
  const handleMpaaToggle = (rating: string) => {
    const current = filters.mpaa_ratings || []
    const updated = current.includes(rating)
      ? current.filter((r) => r !== rating)
      : [...current, rating]
    onFilterChange('mpaa_ratings', updated.length > 0 ? updated : undefined)
  }

  // Collapsible section component
  const Section = ({
    title,
    expanded,
    onToggle,
    children,
    badge,
  }: {
    title: string
    expanded: boolean
    onToggle: () => void
    children: React.ReactNode
    badge?: number
  }) => (
    <div className="border-t border-gray-200 pt-4">
      <button
        onClick={onToggle}
        className="flex items-center justify-between w-full text-left min-h-[44px] py-1"
      >
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">{title}</h3>
          {badge !== undefined && badge > 0 && (
            <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-brand-primary rounded-full">
              {badge}
            </span>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-gray-500 transform transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {expanded && <div className="mt-3 space-y-4">{children}</div>}
    </div>
  )

  // Content threshold control with local state during drag
  const ContentThresholdControl = ({
    label,
    filterKey,
    value,
    color,
  }: {
    label: string
    filterKey: 'sex_max' | 'violence_max' | 'language_max'
    value: number | null | undefined
    color: string
  }) => {
    const anySelected = isAnySelected(value)

    return (
      <div className="space-y-2">
        <RangeSlider
          label={label}
          min={0} max={10} step={1}
          value={anySelected ? 5 : (value ?? 5)}
          displayValue={(v) => anySelected ? 'Any' : `≤ ${v}`}
          onCommit={(v) => handleContentSliderChange(filterKey, String(v))}
          color={anySelected ? 'text-gray-400' : color}
          accent="accent-brand-primary"
          disabled={anySelected}
        />

        <label className="flex items-center gap-2 text-sm cursor-pointer min-h-[44px] md:min-h-0">
          <input
            type="checkbox"
            checked={anySelected}
            onChange={(e) => handleAnyCheckboxChange(filterKey, e.target.checked)}
            className="w-4 h-4 rounded border-gray-300 text-brand-primary focus:ring-brand-primary cursor-pointer"
          />
          <span className="text-gray-600">No limit</span>
        </label>
      </div>
    )
  }

  // Count active filters
  const activeContentFilters = [filters.sex_max, filters.violence_max, filters.language_max].filter(
    (v) => v !== null && v !== undefined
  ).length
  const activeTraditionalFilters =
    (filters.genres && filters.genres.length > 0 ? 1 : 0) +
    (filters.year_min ? 1 : 0) +
    (filters.year_max ? 1 : 0) +
    (filters.mpaa_ratings && filters.mpaa_ratings.length > 0 ? 1 : 0) +
    (filters.awards_min ? 1 : 0)
  const activeQualityFilters =
    (filters.imdb_min && filters.imdb_min > 0 ? 1 : 0) +
    (filters.rt_min && filters.rt_min > 0 ? 1 : 0) +
    (filters.metacritic_min && filters.metacritic_min > 0 ? 1 : 0)

  return (
    <div className="bg-white rounded-lg shadow-md p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-gray-800">Filters</h2>
        <button
          onClick={onReset}
          className="text-sm text-brand-primary hover:text-blue-700 font-medium min-h-[44px] md:min-h-0 px-2"
        >
          Reset All
        </button>
      </div>

      <div className="space-y-4">
        {/* Content Thresholds Section */}
        <Section
          title="Content Thresholds"
          expanded={contentExpanded}
          onToggle={() => setContentExpanded(!contentExpanded)}
          badge={activeContentFilters}
        >
          <ContentThresholdControl
            label="Sex & Nudity"
            filterKey="sex_max"
            value={filters.sex_max}
            color="text-pink-600"
          />
          <ContentThresholdControl
            label="Violence & Gore"
            filterKey="violence_max"
            value={filters.violence_max}
            color="text-red-600"
          />
          <ContentThresholdControl
            label="Language & Profanity"
            filterKey="language_max"
            value={filters.language_max}
            color="text-orange-600"
          />
        </Section>

        {/* Traditional Filters Section */}
        <Section
          title="Movie Filters"
          expanded={traditionalExpanded}
          onToggle={() => setTraditionalExpanded(!traditionalExpanded)}
          badge={activeTraditionalFilters}
        >
          {/* Genre Multi-Select */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-2">Genres</label>
            <div className="flex flex-wrap gap-1.5 max-h-40 overflow-y-auto">
              {availableGenres.map((genre) => {
                const isSelected = filters.genres?.includes(genre)
                return (
                  <button
                    key={genre}
                    onClick={() => handleGenreToggle(genre)}
                    className={`px-2.5 py-1 text-xs rounded-full font-medium transition-colors min-h-[32px]
                      ${isSelected
                        ? 'bg-brand-primary text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                  >
                    {genre}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Year Range */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-2">Year Range</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="From"
                min={1888}
                max={2100}
                value={filters.year_min ?? ''}
                onChange={(e) =>
                  onFilterChange('year_min', e.target.value ? parseInt(e.target.value) : undefined)
                }
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none
                           focus:border-brand-primary focus:ring-1 focus:ring-brand-primary/30 min-h-[44px] md:min-h-0"
              />
              <span className="text-gray-400 text-sm">–</span>
              <input
                type="number"
                placeholder="To"
                min={1888}
                max={2100}
                value={filters.year_max ?? ''}
                onChange={(e) =>
                  onFilterChange('year_max', e.target.value ? parseInt(e.target.value) : undefined)
                }
                className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none
                           focus:border-brand-primary focus:ring-1 focus:ring-brand-primary/30 min-h-[44px] md:min-h-0"
              />
            </div>
          </div>

          {/* MPAA Rating Multi-Select */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-2">MPAA Rating</label>
            <div className="flex flex-wrap gap-1.5">
              {MPAA_RATINGS.map((rating) => {
                const isSelected = filters.mpaa_ratings?.includes(rating)
                return (
                  <button
                    key={rating}
                    onClick={() => handleMpaaToggle(rating)}
                    className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-colors min-h-[36px]
                      ${isSelected
                        ? 'bg-brand-secondary text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border border-gray-200'
                      }`}
                  >
                    {rating}
                  </button>
                )
              })}
            </div>
          </div>

          {/* Awards Filter */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-2">
              Minimum Awards Won
            </label>
            <input
              type="number"
              placeholder="e.g. 1"
              min={0}
              value={filters.awards_min ?? ''}
              onChange={(e) =>
                onFilterChange('awards_min', e.target.value ? parseInt(e.target.value) : undefined)
              }
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none
                         focus:border-brand-primary focus:ring-1 focus:ring-brand-primary/30 min-h-[44px] md:min-h-0"
            />
          </div>
        </Section>

        {/* Quality Ratings Section */}
        <Section
          title="Quality Ratings"
          expanded={qualityExpanded}
          onToggle={() => setQualityExpanded(!qualityExpanded)}
          badge={activeQualityFilters}
        >
          {/* IMDb Minimum */}
          <RangeSlider
            label="IMDb Rating"
            min={0} max={10} step={0.5}
            value={filters.imdb_min ?? 0}
            displayValue={(v) => v > 0 ? `≥ ${v}` : 'Any'}
            onCommit={(v) => onFilterChange('imdb_min', v > 0 ? v : undefined)}
            color="text-yellow-600" accent="accent-yellow-500"
            ticks={['0', '5', '10']}
          />

          {/* Rotten Tomatoes Minimum */}
          <RangeSlider
            label="Rotten Tomatoes"
            min={0} max={100} step={5}
            value={filters.rt_min ?? 0}
            displayValue={(v) => v > 0 ? `≥ ${v}%` : 'Any'}
            onCommit={(v) => onFilterChange('rt_min', v > 0 ? v : undefined)}
            color="text-red-600" accent="accent-red-500"
            ticks={['0%', '50%', '100%']}
          />

          {/* Metacritic Minimum */}
          <RangeSlider
            label="Metacritic"
            min={0} max={100} step={5}
            value={filters.metacritic_min ?? 0}
            displayValue={(v) => v > 0 ? `≥ ${v}` : 'Any'}
            onCommit={(v) => onFilterChange('metacritic_min', v > 0 ? v : undefined)}
            color="text-green-600" accent="accent-green-500"
            ticks={['0', '50', '100']}
          />
        </Section>

        {/* Apply Button (mobile) */}
        {onApply && (
          <div className="pt-4 border-t border-gray-200 md:hidden">
            <button
              onClick={onApply}
              className="w-full py-3 bg-brand-primary text-white font-semibold rounded-lg
                         hover:bg-blue-600 active:bg-blue-700 transition min-h-[44px]"
            >
              Apply Filters
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default FilterPanel
