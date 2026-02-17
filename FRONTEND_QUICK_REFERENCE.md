# Frontend Components - Quick Reference Guide

## Component Hierarchy

```
SearchPage (Main Page)
├── FilterPanel (Sidebar)
│   └── ContentThresholdControl (Nested)
│       ├── Range Sliders (0-10)
│       └── "Show all" Checkboxes
├── Search Bar (Input Field)
└── Results Section
    ├── Loading State
    ├── Error State
    ├── Movie Grid
    │   └── MovieCard[] (List)
    │       └── ContentBadge[] (3 per card)
    └── Pagination Controls
        ├── Previous Button
        ├── Page Input
        └── Next Button
```

## Component Imports

### SearchPage
```typescript
import { useFilters } from '../hooks/useFilters'
import FilterPanel from '../components/FilterPanel'
import MovieCard from '../components/MovieCard'
import apiClient from '../services/api'
```

### MovieCard
```typescript
import { Movie } from '../types/api.types'
import ContentBadge from './ContentBadge'
```

### FilterPanel
```typescript
import { SearchFilters } from '../types/api.types'
```

## Quick Integration Example

```typescript
// In your component
import { useFilters } from '../hooks/useFilters'
import FilterPanel from '../components/FilterPanel'

const MyComponent = () => {
  const { filters, updateFilter, resetFilters } = useFilters()

  return (
    <FilterPanel
      filters={filters}
      onFilterChange={updateFilter}
      onReset={resetFilters}
    />
  )
}
```

## API Call Pattern

```typescript
const performSearch = async (pageNum: number = 1) => {
  const params: Record<string, string | number> = {
    page: pageNum,
    per_page: 30,
  }

  if (filters.q) params.q = filters.q
  if (filters.sex_max !== null) params.sex_max = filters.sex_max
  if (filters.violence_max !== null) params.violence_max = filters.violence_max
  if (filters.language_max !== null) params.language_max = filters.language_max

  const response = await apiClient.get<SearchResponse>('/movies/search', { params })
  return response.data
}
```

## ContentBadge Colors

| State | Color | Class | RGB |
|-------|-------|-------|-----|
| Within Threshold | Green | `bg-content-safe` | #10b981 |
| Exceeds Threshold | Red | `bg-content-warning` | #ef4444 |
| No Filter Set | Gray | `bg-content-unavailable` | #9ca3af |

## Filter State Structure

```typescript
{
  q?: string // Search query
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
```

## Session Storage Key

```typescript
// Key for sessionStorage
'reel-filter-search-filters'

// Persisted automatically by useFilters hook
```

## Responsive Breakpoints

- **Mobile:** `<640px` - Single column, stacked layout
- **Tablet:** `640px - 1024px` - 2 columns, side-by-side when space
- **Desktop:** `>1024px` - 3-column grid + sidebar

## Key Props Reference

### ContentBadge
```typescript
<ContentBadge
  label="Sex" | "Violence" | "Language"
  score={8}
  threshold={7 | null}
/>
```

### MovieCard
```typescript
<MovieCard
  movie={movieObject}
  sexThreshold={7}
  violenceThreshold={5}
  languageThreshold={3}
/>
```

### FilterPanel
```typescript
<FilterPanel
  filters={filtersObject}
  onFilterChange={(key, value) => {}}
  onReset={() => {}}
/>
```

## Styling Classes

### Common Classes Used
- Containers: `container mx-auto px-4 py-8`
- Cards: `bg-white rounded-lg shadow-lg`
- Buttons: `px-4 py-2 border rounded-lg font-semibold`
- Disabled: `disabled:opacity-50 disabled:cursor-not-allowed`
- Responsive Grid: `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6`

## Testing Checklist

- [ ] Search by title
- [ ] Adjust Sex threshold slider
- [ ] Adjust Violence threshold slider
- [ ] Adjust Language threshold slider
- [ ] Check "Show all" hides thresholds
- [ ] Reset filters clears all
- [ ] Badges show correct colors
- [ ] Pagination works (next/prev)
- [ ] Page number input works
- [ ] Filters persist on reload
- [ ] Mobile layout responsive
- [ ] Error handling works
- [ ] Loading state displays
- [ ] No results message shows

## Common Issues & Solutions

### Issue: Filters not persisting
**Solution:** Ensure useFilters is called at page level, not in a child component

### Issue: Content badges not showing color
**Solution:** Check that thresholds are numbers (0-10), not null/undefined for color logic

### Issue: Movie images not loading
**Solution:** The fallback text is intentionally shown - check poster_url in API response

### Issue: Pagination doesn't work
**Solution:** Ensure `page` param is being passed to API call

### Issue: Filter changes not triggering search
**Solution:** Check that `hasSearched` is true before auto-searching on filter change

---

## File Locations

- Components: `frontend/src/components/`
- Pages: `frontend/src/pages/`
- Types: `frontend/src/types/api.types.ts`
- API Client: `frontend/src/services/api.ts`
- Hooks: `frontend/src/hooks/useFilters.ts`
- Styles: Tailwind (see `frontend/tailwind.config.js`)

---

## Version Info

- React: 18.x
- TypeScript: 5.9.3
- Tailwind CSS: 3.x
- Axios: Latest
- Vite: 5.4.21
