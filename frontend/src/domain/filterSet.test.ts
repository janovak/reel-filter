import { describe, it, expect } from 'vitest'
import { SearchFilters } from '../types/api.types'
import {
  getDefaultFilterSet,
  restoreFilterSet,
  isMemberActive,
  emptyValueFor,
  countActiveFilters,
  totalActiveFilters,
  buildSearchParams,
  filterSetChangeKey,
} from './filterSet'

describe('getDefaultFilterSet', () => {
  it('returns a Filter Set with every member empty', () => {
    const defaults = getDefaultFilterSet()
    expect(defaults.q).toBe('')
    expect(defaults.genres).toEqual([])
    expect(defaults.year_min).toBeUndefined()
    expect(defaults.year_max).toBeUndefined()
    expect(defaults.mpaa_ratings).toEqual([])
    expect(defaults.imdb_min).toBe(0)
    expect(defaults.rt_min).toBe(0)
    expect(defaults.metacritic_min).toBe(0)
    expect(defaults.awards_min).toBeUndefined()
    expect(defaults.sex_max).toBeNull()
    expect(defaults.violence_max).toBeNull()
    expect(defaults.language_max).toBeNull()
    expect(defaults.page).toBe(1)
    expect(defaults.per_page).toBe(30)
  })

  it('does not share array references across calls', () => {
    const a = getDefaultFilterSet()
    const b = getDefaultFilterSet()
    expect(a.genres).not.toBe(b.genres)
    expect(a.mpaa_ratings).not.toBe(b.mpaa_ratings)
    ;(a.genres as string[]).push('Horror')
    expect(b.genres).toEqual([])
  })
})

describe('isMemberActive — active/inactive boundaries', () => {
  const defaults = getDefaultFilterSet()

  it('q is active only for non-blank text', () => {
    expect(isMemberActive({ ...defaults, q: '' }, 'q')).toBe(false)
    expect(isMemberActive({ ...defaults, q: '   ' }, 'q')).toBe(false)
    expect(isMemberActive({ ...defaults, q: undefined }, 'q')).toBe(false)
    expect(isMemberActive({ ...defaults, q: 'matrix' }, 'q')).toBe(true)
  })

  it('genres and mpaa_ratings are active only when non-empty', () => {
    expect(isMemberActive({ ...defaults, genres: [] }, 'genres')).toBe(false)
    expect(isMemberActive({ ...defaults, genres: undefined }, 'genres')).toBe(false)
    expect(isMemberActive({ ...defaults, genres: ['Action'] }, 'genres')).toBe(true)

    expect(isMemberActive({ ...defaults, mpaa_ratings: [] }, 'mpaa_ratings')).toBe(false)
    expect(isMemberActive({ ...defaults, mpaa_ratings: undefined }, 'mpaa_ratings')).toBe(false)
    expect(isMemberActive({ ...defaults, mpaa_ratings: ['PG-13'] }, 'mpaa_ratings')).toBe(true)
  })

  it('year_min and year_max are active whenever set', () => {
    expect(isMemberActive({ ...defaults, year_min: undefined }, 'year_min')).toBe(false)
    expect(isMemberActive({ ...defaults, year_min: 1990 }, 'year_min')).toBe(true)
    expect(isMemberActive({ ...defaults, year_max: undefined }, 'year_max')).toBe(false)
    expect(isMemberActive({ ...defaults, year_max: 2010 }, 'year_max')).toBe(true)
  })

  it('awards_min treats 0 and undefined as inactive', () => {
    expect(isMemberActive({ ...defaults, awards_min: undefined }, 'awards_min')).toBe(false)
    expect(isMemberActive({ ...defaults, awards_min: 0 }, 'awards_min')).toBe(false)
    expect(isMemberActive({ ...defaults, awards_min: 1 }, 'awards_min')).toBe(true)
  })

  it('the three quality members (D1) treat 0 and undefined as the same inactive state', () => {
    const quality = ['imdb_min', 'rt_min', 'metacritic_min'] as const
    for (const member of quality) {
      expect(isMemberActive({ ...defaults, [member]: 0 }, member)).toBe(false)
      expect(isMemberActive({ ...defaults, [member]: undefined }, member)).toBe(false)
      expect(isMemberActive({ ...defaults, [member]: 7 }, member)).toBe(true)
    }
  })

  it('the three Content Thresholds treat 0 as active — "none at all" is a real filter', () => {
    const thresholds = ['sex_max', 'violence_max', 'language_max'] as const
    for (const member of thresholds) {
      expect(isMemberActive({ ...defaults, [member]: 0 }, member)).toBe(true)
      expect(isMemberActive({ ...defaults, [member]: 5 }, member)).toBe(true)
      expect(isMemberActive({ ...defaults, [member]: null }, member)).toBe(false)
      expect(isMemberActive({ ...defaults, [member]: undefined }, member)).toBe(false)
    }
  })

  it('a Content Threshold of 10 means "no limit" and is inactive', () => {
    const thresholds = ['sex_max', 'violence_max', 'language_max'] as const
    for (const member of thresholds) {
      expect(isMemberActive({ ...defaults, [member]: 10 }, member)).toBe(false)
    }
  })
})

describe('restoreFilterSet — D1: all empty representations normalise to one value', () => {
  const quality = ['imdb_min', 'rt_min', 'metacritic_min'] as const

  for (const member of quality) {
    it(`${member}: 0, undefined, and an absent key all restore to 0`, () => {
      expect(restoreFilterSet({ [member]: 0 })[member]).toBe(0)
      expect(restoreFilterSet({ [member]: undefined })[member]).toBe(0)
      expect(restoreFilterSet({})[member]).toBe(0)
    })
  }

  it('a stored value of 10 for a Content Threshold normalises to null (no limit)', () => {
    expect(restoreFilterSet({ sex_max: 10 }).sex_max).toBeNull()
  })
})

describe('restoreFilterSet — D2: merges stored JSON over the defaults', () => {
  it('a stored object missing most keys still restores a complete Filter Set', () => {
    const restored = restoreFilterSet({ genres: ['Horror'] })
    const defaults = getDefaultFilterSet()
    expect(restored.genres).toEqual(['Horror'])
    expect(restored.q).toBe(defaults.q)
    expect(restored.year_min).toBe(defaults.year_min)
    expect(restored.mpaa_ratings).toEqual(defaults.mpaa_ratings)
    expect(restored.imdb_min).toBe(defaults.imdb_min)
    expect(restored.sex_max).toBe(defaults.sex_max)
    expect(restored.page).toBe(defaults.page)
    expect(restored.per_page).toBe(defaults.per_page)
  })

  it('an active value that is present is preserved', () => {
    const restored = restoreFilterSet({ q: 'batman', imdb_min: 7.5, sex_max: 0, page: 3 })
    expect(restored.q).toBe('batman')
    expect(restored.imdb_min).toBe(7.5)
    expect(restored.sex_max).toBe(0)
    expect(restored.page).toBe(3)
  })

  it('null or a non-object restores straight to the defaults', () => {
    expect(restoreFilterSet(null)).toEqual(getDefaultFilterSet())
    expect(restoreFilterSet(undefined)).toEqual(getDefaultFilterSet())
  })

  it('drops keys that are not SearchFilters members', () => {
    const restored = restoreFilterSet({ q: 'batman', totally_unknown_field: 'x' })
    expect(restored).not.toHaveProperty('totally_unknown_field')
    expect(Object.keys(restored).sort()).toEqual(
      Object.keys(getDefaultFilterSet()).sort()
    )
  })
})

describe('buildSearchParams', () => {
  it('omits every inactive member, keeping only page and per_page', () => {
    const params = buildSearchParams(getDefaultFilterSet(), 1)
    expect(params).toEqual({ page: 1, per_page: 30 })
  })

  it('includes an active member and trims free text', () => {
    const filters: SearchFilters = { ...getDefaultFilterSet(), q: '  matrix  ' }
    const params = buildSearchParams(filters, 1)
    expect(params.q).toBe('matrix')
  })

  it('a Content Threshold of 0 is sent — it is not the same as "no limit"', () => {
    const filters: SearchFilters = { ...getDefaultFilterSet(), sex_max: 0 }
    const params = buildSearchParams(filters, 1)
    expect(params.sex_max).toBe(0)
  })

  it('a Content Threshold of 10 ("no limit") is omitted, not sent as 10', () => {
    const filters: SearchFilters = { ...getDefaultFilterSet(), violence_max: 10 }
    const params = buildSearchParams(filters, 1)
    expect(params).not.toHaveProperty('violence_max')
  })

  it('genres and mpaa_ratings serialise as arrays, for repeated-key params', () => {
    const filters: SearchFilters = {
      ...getDefaultFilterSet(),
      genres: ['Action', 'Drama'],
      mpaa_ratings: ['PG-13', 'R'],
    }
    const params = buildSearchParams(filters, 1)
    expect(params.genres).toEqual(['Action', 'Drama'])
    expect(params.mpaa_ratings).toEqual(['PG-13', 'R'])
  })

  it('uses the explicit page argument, not filters.page', () => {
    const filters: SearchFilters = { ...getDefaultFilterSet(), page: 1 }
    const params = buildSearchParams(filters, 4)
    expect(params.page).toBe(4)
  })

  it('falls back to 30 per_page when per_page is falsy', () => {
    const filters: SearchFilters = { ...getDefaultFilterSet(), per_page: 0 }
    const params = buildSearchParams(filters, 1)
    expect(params.per_page).toBe(30)
  })
})

describe('emptyValueFor', () => {
  it('matches the default (empty) Filter Set for every member', () => {
    const defaults = getDefaultFilterSet()
    expect(emptyValueFor('imdb_min')).toBe(defaults.imdb_min)
    expect(emptyValueFor('sex_max')).toBe(defaults.sex_max)
    expect(emptyValueFor('awards_min')).toBe(defaults.awards_min)
    expect(emptyValueFor('genres')).toEqual(defaults.genres)
  })

  it('returns a fresh array each call for array members', () => {
    const first = emptyValueFor('genres') as string[]
    const second = emptyValueFor('genres') as string[]
    expect(first).not.toBe(second)
    first.push('Horror')
    expect(second).toEqual([])
  })
})

describe('countActiveFilters and totalActiveFilters', () => {
  it('counts each section independently', () => {
    const filters: SearchFilters = {
      ...getDefaultFilterSet(),
      sex_max: 0,
      violence_max: 5,
      genres: ['Action'],
      year_min: 1990,
      imdb_min: 7,
    }
    expect(countActiveFilters(filters, 'content')).toBe(2)
    expect(countActiveFilters(filters, 'traditional')).toBe(2)
    expect(countActiveFilters(filters, 'quality')).toBe(1)
  })

  it('totalActiveFilters sums every section but excludes q', () => {
    const filters: SearchFilters = {
      ...getDefaultFilterSet(),
      q: 'matrix',
      sex_max: 0,
      genres: ['Action'],
      imdb_min: 7,
    }
    expect(totalActiveFilters(filters)).toBe(3)
  })

  it('an all-empty Filter Set counts zero everywhere', () => {
    const defaults = getDefaultFilterSet()
    expect(totalActiveFilters(defaults)).toBe(0)
    expect(countActiveFilters(defaults, 'content')).toBe(0)
    expect(countActiveFilters(defaults, 'traditional')).toBe(0)
    expect(countActiveFilters(defaults, 'quality')).toBe(0)
  })
})

describe('filterSetChangeKey', () => {
  const defaults = getDefaultFilterSet()

  it('differs when a search-affecting member differs', () => {
    const changed: SearchFilters = { ...defaults, q: 'matrix' }
    expect(filterSetChangeKey(changed)).not.toBe(filterSetChangeKey(defaults))
  })

  it('differs for every search-affecting member in turn', () => {
    const cases: Array<Partial<SearchFilters>> = [
      { q: 'matrix' },
      { genres: ['Action'] },
      { year_min: 1990 },
      { year_max: 2010 },
      { mpaa_ratings: ['R'] },
      { imdb_min: 7 },
      { rt_min: 80 },
      { metacritic_min: 70 },
      { awards_min: 2 },
      { sex_max: 0 },
      { violence_max: 3 },
      { language_max: 3 },
    ]
    for (const change of cases) {
      const changed: SearchFilters = { ...defaults, ...change }
      expect(filterSetChangeKey(changed)).not.toBe(filterSetChangeKey(defaults))
    }
  })

  it('does not change for page alone', () => {
    const page1: SearchFilters = { ...defaults, page: 1 }
    const page5: SearchFilters = { ...defaults, page: 5 }
    expect(filterSetChangeKey(page1)).toBe(filterSetChangeKey(page5))
  })

  it('does not change for per_page alone', () => {
    const a: SearchFilters = { ...defaults, per_page: 30 }
    const b: SearchFilters = { ...defaults, per_page: 60 }
    expect(filterSetChangeKey(a)).toBe(filterSetChangeKey(b))
  })

  it('treats equivalent empty representations as identical (no spurious re-search)', () => {
    const zero: SearchFilters = { ...defaults, imdb_min: 0 }
    const undef: SearchFilters = { ...defaults, imdb_min: undefined }
    expect(filterSetChangeKey(zero)).toBe(filterSetChangeKey(undef))

    const nullSex: SearchFilters = { ...defaults, sex_max: null }
    const undefSex: SearchFilters = { ...defaults, sex_max: undefined }
    expect(filterSetChangeKey(nullSex)).toBe(filterSetChangeKey(undefSex))

    const noLimit: SearchFilters = { ...defaults, violence_max: 10 }
    expect(filterSetChangeKey(noLimit)).toBe(filterSetChangeKey(defaults))
  })
})
