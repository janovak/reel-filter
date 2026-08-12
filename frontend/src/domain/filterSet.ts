/**
 * The Filter Set domain module.
 *
 * A Filter Set is the complete set of criteria one search runs under: title
 * text, genres, year range, MPAA Ratings, minimum quality ratings, minimum
 * awards, and the three Content Threshold members, plus pagination. See
 * CONTEXT.md for the full vocabulary.
 *
 * A member of a Filter Set is "active" when the user has set it, and "empty"
 * otherwise. Historically that rule was re-typed at four call sites in the
 * UI, each with its own idea of what "empty" looks like for a given member
 * (`0`, `null`, `[]`, `undefined`) — this module is the one place that rule
 * now lives. Everything else — the page, the panel, the badge counts, the
 * empty state — reads from it instead of re-deriving it.
 *
 * Plain TypeScript. No React, no HTTP. UI-lifecycle concerns (sessionStorage,
 * the search debounce, the page-reset-on-change behaviour) stay outside this
 * module, in the hooks and components that own that lifecycle.
 */
import { SearchFilters } from '../types/api.types'

export type FilterSetSection = 'content' | 'traditional' | 'quality'

/**
 * The members of a Filter Set that participate in "is this filter active"
 * reasoning. Excludes `page` and `per_page` — those are pagination state,
 * not filter criteria; they are always sent, never "active" or "empty".
 */
export type FilterSetMember =
  | 'q'
  | 'genres'
  | 'year_min'
  | 'year_max'
  | 'mpaa_ratings'
  | 'imdb_min'
  | 'rt_min'
  | 'metacritic_min'
  | 'awards_min'
  | 'sex_max'
  | 'violence_max'
  | 'language_max'

export const FILTER_SET_MEMBERS: readonly FilterSetMember[] = [
  'q',
  'genres',
  'year_min',
  'year_max',
  'mpaa_ratings',
  'imdb_min',
  'rt_min',
  'metacritic_min',
  'awards_min',
  'sex_max',
  'violence_max',
  'language_max',
]

const FILTER_SET_SECTIONS: readonly FilterSetSection[] = ['content', 'traditional', 'quality']

interface FilterMemberSpec<V> {
  /**
   * The one value that means "the user has not set this member". Also the
   * value this member holds in the default Filter Set — a fresh Filter Set
   * is, by definition, one where every member is empty.
   */
  empty: V
  /** Whether a given value counts as set (active) for this member. */
  isActive: (value: V) => boolean
  /**
   * Which FilterPanel section this member's badge belongs to. `q` has none
   * — title text lives in the SearchBar, not the FilterPanel.
   */
  section?: FilterSetSection
}

/**
 * The single table this module is built around. One row per Filter Set
 * member, one definition of "active" each. Nothing outside this table
 * re-derives what counts as empty.
 */
const MEMBERS: { [K in FilterSetMember]: FilterMemberSpec<SearchFilters[K]> } = {
  q: {
    empty: '',
    isActive: (v) => typeof v === 'string' && v.trim().length > 0,
  },
  genres: {
    empty: [],
    isActive: (v) => Array.isArray(v) && v.length > 0,
    section: 'traditional',
  },
  year_min: {
    empty: undefined,
    isActive: (v) => typeof v === 'number',
    section: 'traditional',
  },
  year_max: {
    empty: undefined,
    isActive: (v) => typeof v === 'number',
    section: 'traditional',
  },
  mpaa_ratings: {
    empty: [],
    isActive: (v) => Array.isArray(v) && v.length > 0,
    section: 'traditional',
  },
  awards_min: {
    // Not `0` — the awards number input shows a blank field with a
    // placeholder when unset, and `0 ?? ''` would render "0" instead.
    empty: undefined,
    isActive: (v) => typeof v === 'number' && v > 0,
    section: 'traditional',
  },
  imdb_min: {
    // D1: this member had two empty values, `0` (the old default) and
    // `undefined` (what the slider wrote at zero). `0` is the one the
    // sliders always display for "unset" either way, so it is the value
    // this module normalises to and writes.
    empty: 0,
    isActive: (v) => typeof v === 'number' && v > 0,
    section: 'quality',
  },
  rt_min: {
    empty: 0,
    isActive: (v) => typeof v === 'number' && v > 0,
    section: 'quality',
  },
  metacritic_min: {
    empty: 0,
    isActive: (v) => typeof v === 'number' && v > 0,
    section: 'quality',
  },
  sex_max: {
    // A Content Threshold ranges over the same 0-10 scale as a Content
    // Score. `0` is a real, active threshold — "none at all" — and must
    // not be treated as empty. `10` is the slider's "No limit" position;
    // since no Content Score exceeds 10, a `<= 10` threshold filters
    // nothing, so it means the same thing as unset and is treated that way.
    empty: null,
    isActive: (v) => typeof v === 'number' && v < 10,
    section: 'content',
  },
  violence_max: {
    empty: null,
    isActive: (v) => typeof v === 'number' && v < 10,
    section: 'content',
  },
  language_max: {
    empty: null,
    isActive: (v) => typeof v === 'number' && v < 10,
    section: 'content',
  },
}

const DEFAULT_PAGE = 1
const DEFAULT_PER_PAGE = 30

/** A fresh copy of a member's empty value — arrays are never shared by reference. */
function emptyCopy<K extends FilterSetMember>(key: K): SearchFilters[K] {
  const value = MEMBERS[key].empty
  return Array.isArray(value) ? ([...value] as SearchFilters[K]) : value
}

/**
 * The canonical default Filter Set. Every member is empty — there is no
 * other kind of "default" for a Filter Set than "nothing is set yet".
 */
export function getDefaultFilterSet(): SearchFilters {
  return {
    q: emptyCopy('q'),
    genres: emptyCopy('genres'),
    year_min: emptyCopy('year_min'),
    year_max: emptyCopy('year_max'),
    mpaa_ratings: emptyCopy('mpaa_ratings'),
    imdb_min: emptyCopy('imdb_min'),
    rt_min: emptyCopy('rt_min'),
    metacritic_min: emptyCopy('metacritic_min'),
    awards_min: emptyCopy('awards_min'),
    sex_max: emptyCopy('sex_max'),
    violence_max: emptyCopy('violence_max'),
    language_max: emptyCopy('language_max'),
    page: DEFAULT_PAGE,
    per_page: DEFAULT_PER_PAGE,
  }
}

/** The value writers should write for this member when the user clears it. */
export function emptyValueFor<K extends FilterSetMember>(key: K): SearchFilters[K] {
  return emptyCopy(key)
}

/** Whether this member of the given Filter Set is active (set by the user). */
export function isMemberActive<K extends FilterSetMember>(filters: SearchFilters, key: K): boolean {
  return MEMBERS[key].isActive(filters[key])
}

/** How many members in one FilterPanel section are active. */
export function countActiveFilters(filters: SearchFilters, section: FilterSetSection): number {
  return FILTER_SET_MEMBERS.filter(
    (key) => MEMBERS[key].section === section && isMemberActive(filters, key)
  ).length
}

/**
 * How many members are active in total, across every section. Excludes `q`
 * — it has no section and is not part of any FilterPanel/badge count, same
 * as today's hand-written `activeFilterCount`.
 */
export function totalActiveFilters(filters: SearchFilters): number {
  return FILTER_SET_SECTIONS.reduce((sum, section) => sum + countActiveFilters(filters, section), 0)
}

function normalizeMember<K extends FilterSetMember>(
  key: K,
  raw: unknown,
  fallback: SearchFilters[K]
): SearchFilters[K] {
  if (raw === undefined) return fallback
  const value = raw as SearchFilters[K]
  return MEMBERS[key].isActive(value) ? value : emptyCopy(key)
}

function normalizePositiveNumber(raw: unknown, fallback: number): number {
  return typeof raw === 'number' && Number.isFinite(raw) && raw >= 1 ? raw : fallback
}

/**
 * Restore a Filter Set from stored JSON (e.g. sessionStorage), merged over
 * the defaults. Fixes D2: a member missing from `stored` — because it was
 * `undefined` when `JSON.stringify` dropped it, or because it is a member
 * added to `SearchFilters` after this was saved — falls back to its default
 * rather than vanishing from the restored Filter Set. Keys in `stored` that
 * are not Filter Set members are dropped.
 */
export function restoreFilterSet(stored: unknown): SearchFilters {
  const source: Record<string, unknown> =
    stored !== null && typeof stored === 'object' ? (stored as Record<string, unknown>) : {}
  const defaults = getDefaultFilterSet()

  return {
    q: normalizeMember('q', source.q, defaults.q),
    genres: normalizeMember('genres', source.genres, defaults.genres),
    year_min: normalizeMember('year_min', source.year_min, defaults.year_min),
    year_max: normalizeMember('year_max', source.year_max, defaults.year_max),
    mpaa_ratings: normalizeMember('mpaa_ratings', source.mpaa_ratings, defaults.mpaa_ratings),
    imdb_min: normalizeMember('imdb_min', source.imdb_min, defaults.imdb_min),
    rt_min: normalizeMember('rt_min', source.rt_min, defaults.rt_min),
    metacritic_min: normalizeMember('metacritic_min', source.metacritic_min, defaults.metacritic_min),
    awards_min: normalizeMember('awards_min', source.awards_min, defaults.awards_min),
    sex_max: normalizeMember('sex_max', source.sex_max, defaults.sex_max),
    violence_max: normalizeMember('violence_max', source.violence_max, defaults.violence_max),
    language_max: normalizeMember('language_max', source.language_max, defaults.language_max),
    page: normalizePositiveNumber(source.page, DEFAULT_PAGE),
    per_page: normalizePositiveNumber(source.per_page, DEFAULT_PER_PAGE),
  }
}

export type SearchParams = Record<string, string | number | string[]>

/**
 * The query params for a search request: every active member, in the shape
 * `apiClient` expects (arrays stay arrays, so `paramsSerializer: { indexes:
 * null }` turns them into repeated keys — `genres=Action&genres=Drama`).
 * Inactive members are omitted entirely. `page` is a parameter of the
 * request, not a member of the Filter Set being searched with, so it is
 * passed in separately rather than read from `filters.page` — see
 * SearchPage's `performSearch`, which searches a target page before that
 * page is committed back into the Filter Set.
 */
export function buildSearchParams(filters: SearchFilters, page: number): SearchParams {
  const params: SearchParams = {
    page,
    per_page: filters.per_page || DEFAULT_PER_PAGE,
  }

  if (isMemberActive(filters, 'q')) {
    params.q = (filters.q as string).trim()
  }
  if (isMemberActive(filters, 'genres')) {
    params.genres = filters.genres as string[]
  }
  if (isMemberActive(filters, 'year_min')) {
    params.year_min = filters.year_min as number
  }
  if (isMemberActive(filters, 'year_max')) {
    params.year_max = filters.year_max as number
  }
  if (isMemberActive(filters, 'mpaa_ratings')) {
    params.mpaa_ratings = filters.mpaa_ratings as string[]
  }
  if (isMemberActive(filters, 'imdb_min')) {
    params.imdb_min = filters.imdb_min as number
  }
  if (isMemberActive(filters, 'rt_min')) {
    params.rt_min = filters.rt_min as number
  }
  if (isMemberActive(filters, 'metacritic_min')) {
    params.metacritic_min = filters.metacritic_min as number
  }
  if (isMemberActive(filters, 'awards_min')) {
    params.awards_min = filters.awards_min as number
  }
  if (isMemberActive(filters, 'sex_max')) {
    params.sex_max = filters.sex_max as number
  }
  if (isMemberActive(filters, 'violence_max')) {
    params.violence_max = filters.violence_max as number
  }
  if (isMemberActive(filters, 'language_max')) {
    params.language_max = filters.language_max as number
  }

  return params
}

/**
 * A stable key that changes exactly when a search-affecting member of the
 * Filter Set changes. Every inactive member is collapsed to its canonical
 * empty value first, so two different spellings of "unset" (e.g. `0` vs.
 * `undefined` on a quality member) never produce two different keys. `page`
 * and `per_page` are not Filter Set members and are never part of this key
 * — paging through results must not, by itself, re-trigger a search.
 */
export function filterSetChangeKey(filters: SearchFilters): string {
  return FILTER_SET_MEMBERS.map((key) => {
    const value = isMemberActive(filters, key) ? filters[key] : MEMBERS[key].empty
    return Array.isArray(value) ? value.join(',') : String(value)
  }).join('|')
}
