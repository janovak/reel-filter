/**
 * SearchBar Component
 * Title search input with debounced search and responsive design
 */

import { useState, useEffect, useRef } from 'react'

interface SearchBarProps {
  value: string
  onChange: (query: string) => void
  onSearch: () => void
  placeholder?: string
}

const SearchBar = ({ value, onChange, onSearch, placeholder = 'Search movies by title...' }: SearchBarProps) => {
  const [localValue, setLocalValue] = useState(value)
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Sync with external value
  useEffect(() => {
    setLocalValue(value)
  }, [value])

  const handleChange = (newValue: string) => {
    setLocalValue(newValue)

    // Debounce: wait 400ms after user stops typing
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }
    debounceTimer.current = setTimeout(() => {
      onChange(newValue)
    }, 400)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current)
      }
      onChange(localValue)
      onSearch()
    }
  }

  const handleClear = () => {
    setLocalValue('')
    onChange('')
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current)
    }
  }

  return (
    <div className="relative w-full">
      {/* Search icon */}
      <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
        <svg
          className="w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      <input
        type="text"
        value={localValue}
        onChange={(e) => handleChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="w-full pl-12 pr-12 py-3 text-base md:text-lg border-2 border-gray-300 rounded-xl
                   focus:outline-none focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20
                   transition-all duration-200 bg-white shadow-sm"
        aria-label="Search movies"
      />

      {/* Clear button */}
      {localValue && (
        <button
          onClick={handleClear}
          className="absolute inset-y-0 right-0 flex items-center pr-4 text-gray-400 hover:text-gray-600
                     min-w-[44px] min-h-[44px] justify-center"
          aria-label="Clear search"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  )
}

export default SearchBar
