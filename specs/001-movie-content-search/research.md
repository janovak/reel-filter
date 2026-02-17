# Research Findings: Movie Content-Aware Search

**Date**: 2025-01-23  
**Status**: Complete  
**Purpose**: Resolve all "NEEDS CLARIFICATION" items from Technical Context and establish technology stack with best practices.

---

## Technology Stack

### Backend Framework

**Decision**: Python 3.11+ with FastAPI

**Rationale**: 
- **Web Scraping Advantage**: BeautifulSoup + requests is battle-tested for Kids-in-Mind scraping, with superior edge case handling (lxml, Selenium for dynamic content) compared to Node's Cheerio. Kids-in-Mind scraping reliability is critical to MVP success.
- **Async Job Scheduling**: Celery + Redis is the gold standard for weekly refresh scheduling with retry logic, error logging, and monitoring. Superior maturity compared to Node's Bull.
- **Database ORM**: SQLAlchemy outperforms Sequelize/TypeORM for complex queries across 9 filter fields (genre, year, ratings, content scores), with better indexing control and performance optimization.
- **REST API Performance**: FastAPI is faster than Express, includes auto-generated OpenAPI docs, and excels at async operations. Built-in validation and dependency injection reduce boilerplate.
- **Fuzzy Matching**: RapidFuzz (Python) outperforms JavaScript alternatives for >90% accuracy requirement on title/year matching.
- **Deployment**: FastAPI containerizes cleanly; weekly cron jobs integrate naturally with Python environments.

**Alternatives Considered**:
- **Node.js + Express/NestJS**: Good option, but weaker web scraping ecosystem and less mature async job scheduling (Bull vs Celery)
- **Flask**: More lightweight than FastAPI but lacks built-in async support and auto-generated API docs

**Primary Dependencies**:
- FastAPI 0.109+ (web framework)
- SQLAlchemy 2.0+ (ORM)
- httpx (async HTTP client for OMDb API)
- BeautifulSoup4 + lxml (web scraping)
- Celery + Redis (async task queue)
- RapidFuzz (fuzzy string matching)
- Pydantic (data validation)

---

### Frontend Framework

**Decision**: React 18+ with TypeScript

**Rationale**:
- **Component Reusability**: MovieCard, FilterPanel, SearchBar, ContentBadge components align perfectly with React's component model and JSX clarity
- **Session Storage**: React Context API + custom `useFilters` hook provides elegant filter persistence without external state library overhead
- **Mobile Responsiveness**: Proven ecosystem with seamless Tailwind CSS integration; 375px minimum width easily achieved with mobile-first approach
- **Performance**: Virtual scrolling libraries (react-window) enable efficient pagination of 20-30 items; filter updates consistently <500ms with proper memoization (useMemo, useCallback)
- **CSS Framework Compatibility**: React has largest component library ecosystem for all three candidate frameworks (Tailwind, Bootstrap, Material-UI)
- **Community Support**: Largest ecosystem for content filtering patterns and complex UI interactions

**Alternatives Considered**:
- **Vue 3**: Simpler syntax, Pinia for state management is excellent, but smaller ecosystem for complex filtering UIs
- **Svelte**: Best performance characteristics, but smallest ecosystem and fewer mature component libraries

**Primary Dependencies**:
- React 18.2+
- TypeScript 5.0+
- Tailwind CSS 3.0+ (utility-first CSS framework)
- React Router 6+ (client-side routing)
- Axios (HTTP client for API calls)
- React Testing Library (component testing)

---

### Database

**Decision**: PostgreSQL 15+

**Rationale**:
- **Full-Text Search**: Native GIN/GiST indexes with `tsvector` support for fast phrase matching on movie titles, superior to MySQL's basic full-text search
- **JSON Support**: JSONB with native indexing (fastest implementation) for awards/metadata queries, crucial for flexible metadata storage
- **Composite Indexes**: B-tree, BRIN, GiST fully optimized for 9-field filtering scenario with excellent partial index support
- **Array Handling**: First-class array type support with GIN indexes for genre filtering (`genre && ARRAY['Action','Sci-Fi']`)
- **Performance**: Easily meets <1s query target at 5,000 records; scales well if dataset grows
- **SQLAlchemy Integration**: First-class support with mature connection pooling and async capabilities

**Alternatives Considered**:
- **SQLite**: Excellent for MVP (zero DevOps), but limited full-text search, no JSON indexing, and weaker concurrent write handling. Valid for initial development but plan migration path.
- **MySQL**: Good alternative, but slower JSON indexing and weaker full-text search compared to PostgreSQL

**Database Schema Considerations**:
- Use PostgreSQL array type for genres (enables GIN indexing)
- Use JSONB for awards metadata (flexible structure, indexed queries)
- Implement partial indexes for content-filtered queries (WHERE content_score IS NOT NULL)

---

## Integration Patterns

### OMDb API Best Practices

**Rate Limiting Strategy**:
- OMDb API has rate limits based on API key tier (free: 1,000 daily requests)
- Implement request throttling: max 10 requests/second during weekly refresh
- Use exponential backoff: 1s, 2s, 4s, 8s delays on rate limit errors (HTTP 429)
- Cache API responses in database to minimize subsequent calls

**Error Handling Pattern**:
```python
# Retry decorator with exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_omdb_movie(title, year):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(OMDB_URL, params={...})
        response.raise_for_status()
        return response.json()
```

**Caching Strategy**:
- Store all OMDb responses in database (avoid duplicate API calls)
- Refresh existing movies weekly (only fetch new releases or missing movies)
- Implement ETags if OMDb supports them (avoid unnecessary data transfer)

**Bulk vs On-Demand**:
- Weekly refresh: Bulk fetch for all tracked movies (batch by year/genre)
- Real-time search: Return cached database results only (no live API calls during user searches)

---

### Kids-in-Mind Web Scraping

**Library**: BeautifulSoup4 + lxml parser

**Scraping Architecture**:
```python
from bs4 import BeautifulSoup
import httpx

async def scrape_content_scores(movie_title, year):
    # 1. Search for movie on Kids-in-Mind
    search_url = f"https://kids-in-mind.com/search.htm?q={movie_title}"
    
    # 2. Parse search results, find best match
    # 3. Extract detail page URL
    # 4. Parse detail page for content scores (sex, violence, language)
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(detail_url)
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract scores from specific HTML structure
        sex_score = extract_score(soup, 'sex')
        violence_score = extract_score(soup, 'violence')
        language_score = extract_score(soup, 'language')
        
        return ContentScore(sex_score, violence_score, language_score)
```

**Anti-Scraping Measures**:
- **Rate Limiting**: Max 1 request per 2 seconds (30 requests/minute) to avoid IP blocking
- **User-Agent Rotation**: Use realistic browser user agents
- **Retry Logic**: Exponential backoff on 429/503 errors (same as OMDb)
- **Session Management**: Maintain session cookies if site requires them
- **Error Handling**: Gracefully handle HTML structure changes (log failures, flag for manual review)

**Data Validation**:
```python
def validate_content_score(score):
    """Ensure scraped content scores are valid 0-10 integers"""
    if not isinstance(score, int) or score < 0 or score > 10:
        raise ValueError(f"Invalid content score: {score}")
    return score
```

**Ethical Scraping**:
- Respect robots.txt (check if scraping is allowed)
- Include contact information in User-Agent header
- Implement rate limiting to avoid server overload
- Cache results to minimize repeat requests

**Handling Site Structure Changes**:
- Version the scraper code (track HTML selectors by version)
- Implement integration tests with saved HTML fixtures
- Monitor scrape success rate (alert if <90%)
- Maintain manual review queue for failed scrapes

---

### Fuzzy Matching Algorithm

**Decision**: Hybrid RapidFuzz approach (TokenSort + Partial Ratio)

**Algorithm**:
```python
from rapidfuzz import fuzz

def match_movie_titles(omdb_title, kim_title, omdb_year, kim_year):
    """
    Match movie titles between OMDb and Kids-in-Mind
    Returns: (confidence_score, should_auto_match, needs_review)
    """
    # Token-based matching (handles subtitle variations, word order)
    token_score = fuzz.token_sort_ratio(omdb_title, kim_title)
    
    # Partial matching (handles partial title matches)
    partial_score = fuzz.partial_ratio(omdb_title, kim_title)
    
    # Take best of both approaches
    title_score = max(token_score, partial_score)
    
    # Year matching bonus (±1 year tolerance per spec clarification)
    year_match_bonus = 100 if abs(omdb_year - kim_year) <= 1 else 0
    
    # Weighted final score
    final_score = title_score * 0.7 + year_match_bonus * 0.3
    
    # Decision thresholds
    should_auto_match = final_score > 88  # >90% accuracy target
    needs_review = 75 <= final_score <= 88
    
    return final_score, should_auto_match, needs_review
```

**Confidence Thresholds**:
- **>88**: Auto-match (high confidence, meets >90% accuracy requirement)
- **75-88**: Manual review queue (catches edge cases like foreign titles, remakes)
- **<75**: Skip (too ambiguous, likely different movies)

**Handling Edge Cases**:
- **Subtitle Variations**: TokenSort handles reordering ("The Dark Knight" vs "Dark Knight, The")
- **Year Mismatches**: Apply ±1 year tolerance (exact title + year within 1 = high-confidence match per spec clarification)
- **Foreign Titles**: Manual review queue catches these (different language titles)
- **Remakes/Sequels**: Year matching prevents false positives ("King Kong" 1933 vs 2005)

**Accuracy Target**: >90% auto-match accuracy with <5% false positive rate

**Alternatives Considered**:
- **fuzzywuzzy**: Predecessor to RapidFuzz, 4-10x slower
- **difflib (Python standard library)**: Doesn't handle token reordering
- **Jaro-Winkler alone**: Misses token-level variations (subtitles, word order)

---

## Performance Optimizations

### Database Indexing Strategy

**PostgreSQL Index Design**:

1. **Single-Field Indexes** (independent filters):
```sql
-- Individual lookups (frequent independent filtering)
CREATE INDEX idx_year ON movies (year);
CREATE INDEX idx_mpaa_rating ON movies (mpaa_rating);
CREATE INDEX idx_imdb_rating ON movies (imdb_rating);
CREATE INDEX idx_rt_rating ON movies (rt_rating);
CREATE INDEX idx_metacritic_rating ON movies (metacritic_rating);

-- Content scores (range queries)
CREATE INDEX idx_sex_nudity ON content_scores (sex_nudity);
CREATE INDEX idx_violence_gore ON content_scores (violence_gore);
CREATE INDEX idx_language_profanity ON content_scores (language_profanity);

-- Array field (GIN index for genre filtering)
CREATE INDEX idx_genre_gin ON movies USING GIN (genre);
```

2. **Full-Text Search Index**:
```sql
-- Title search with GIN index
CREATE INDEX idx_title_fts ON movies USING GIN (to_tsvector('english', title));

-- Usage in queries:
-- SELECT * FROM movies WHERE to_tsvector('english', title) @@ to_tsquery('matrix');
```

3. **Composite Indexes** (common filter combinations):
```sql
-- Most frequent filter pattern (traditional + content)
CREATE INDEX idx_filters_common ON movies 
    (mpaa_rating, year, imdb_rating);

-- Content-focused filtering
CREATE INDEX idx_content_composite ON content_scores 
    (sex_nudity, violence_gore, language_profanity);
```

4. **Partial Indexes** (optimize for common conditions):
```sql
-- Only index movies with content scores (reduces index size)
CREATE INDEX idx_content_available ON content_scores 
    (sex_nudity, violence_gore, language_profanity)
    WHERE sex_nudity IS NOT NULL;

-- Only index rated movies
CREATE INDEX idx_rated_movies ON movies (imdb_rating)
    WHERE imdb_rating > 0;
```

**Query Optimization Approach**:
- Use `EXPLAIN ANALYZE` to verify index usage
- Implement pagination with `LIMIT` and `OFFSET` (20-30 movies per page)
- Use database connection pooling (SQLAlchemy's `create_engine` with pool_size=5)
- Cache frequently accessed queries (Redis for popular filter combinations)
- Monitor slow query log (queries >500ms)

**Expected Performance**:
- At 5,000 records, all indexes fit in memory (~50MB total)
- Multi-field filter queries: <100ms
- Full-text search queries: <200ms
- Combined filters + pagination: <500ms (well under 1s target)

---

## Testing Strategy

### Backend Testing (Python FastAPI)

**Unit Tests**: pytest

**Framework**: pytest 7.0+ with plugins
- pytest-asyncio (async test support)
- pytest-cov (code coverage)
- pytest-mock (mocking)

**Example Structure**:
```python
# tests/unit/services/test_movie_service.py
import pytest
from app.services.movie_service import MovieService

@pytest.fixture
def movie_service():
    return MovieService()

@pytest.mark.asyncio
async def test_search_movies_by_genre(movie_service):
    results = await movie_service.search(genres=['Action'])
    assert all(movie.genre.contains('Action') for movie in results)
```

**Integration Tests**: pytest + TestClient

**API Testing**:
```python
# tests/integration/test_search_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_with_content_filters():
    response = client.get("/api/movies/search", params={
        "sex_max": 5,
        "violence_max": 6,
        "language_max": 7
    })
    assert response.status_code == 200
    movies = response.json()["movies"]
    assert all(m["content_score"]["sex_nudity"] <= 5 for m in movies)
```

**API Mocking**: responses + httpx-mock

**Mock External APIs**:
```python
# tests/unit/integrations/test_omdb_client.py
import responses
from app.integrations.omdb_client import OMDbClient

@responses.activate
def test_fetch_movie_success():
    responses.add(
        responses.GET,
        "http://www.omdbapi.com/",
        json={"Title": "The Matrix", "Year": "1999"},
        status=200
    )
    
    client = OMDbClient()
    movie = client.fetch_movie("The Matrix", 1999)
    assert movie.title == "The Matrix"
```

**Contract Testing**: openapi-spec-validator + Pact

**OpenAPI Validation**:
```python
# tests/contract/test_openapi_spec.py
from openapi_spec_validator import validate_spec
import yaml

def test_openapi_spec_valid():
    with open("shared/contracts/api.yaml") as f:
        spec = yaml.safe_load(f)
    validate_spec(spec)  # Raises exception if invalid
```

---

### Frontend Testing (React)

**Component Tests**: Vitest + React Testing Library

**Framework**: Vitest 1.0+ (10x faster than Jest, ESM-native)

**Example Structure**:
```javascript
// tests/components/MovieCard.test.jsx
import { render, screen } from '@testing-library/react'
import { MovieCard } from '@/components/MovieCard'

test('displays content badges with correct colors', () => {
  const movie = {
    title: 'The Matrix',
    content_score: { sex_nudity: 3, violence_gore: 8, language_profanity: 5 }
  }
  const thresholds = { sex_max: 5, violence_max: 6, language_max: 7 }
  
  render(<MovieCard movie={movie} thresholds={thresholds} />)
  
  // Sex badge should be green (3 <= 5)
  expect(screen.getByText('3')).toHaveClass('badge-green')
  
  // Violence badge should be red (8 > 6)
  expect(screen.getByText('8')).toHaveClass('badge-red')
})
```

**E2E Tests**: Playwright

**Framework**: Playwright 1.40+ (superior cross-browser support, API mocking)

**Example Structure**:
```javascript
// tests/e2e/search-workflow.spec.js
import { test, expect } from '@playwright/test'

test('search with content filters shows only matching movies', async ({ page }) => {
  await page.goto('http://localhost:3000')
  
  // Set content thresholds
  await page.fill('[data-testid="sex-threshold"]', '5')
  await page.fill('[data-testid="violence-threshold"]', '6')
  await page.fill('[data-testid="language-threshold"]', '7')
  
  // Perform search
  await page.fill('[data-testid="search-input"]', 'action')
  await page.click('[data-testid="search-button"]')
  
  // Verify results respect thresholds
  await expect(page.locator('.movie-card')).toHaveCount(20)  // Pagination
  
  // Check first result has valid content scores
  const firstCard = page.locator('.movie-card').first()
  const sexScore = await firstCard.locator('[data-testid="sex-score"]').textContent()
  expect(Number(sexScore)).toBeLessThanOrEqual(5)
})
```

**API Request Mocking** (Playwright):
```javascript
test('handles API errors gracefully', async ({ page }) => {
  // Mock failed API response
  await page.route('**/api/movies/search', route => route.fulfill({
    status: 500,
    body: JSON.stringify({ error: 'Database connection failed' })
  }))
  
  await page.goto('http://localhost:3000')
  await page.fill('[data-testid="search-input"]', 'test')
  await page.click('[data-testid="search-button"]')
  
  // Verify error message displayed
  await expect(page.locator('[data-testid="error-message"]')).toContainText('Unable to load movies')
})
```

---

### Test Coverage Goals

- **Backend**: 80% code coverage (pytest-cov)
  - Critical paths (search, filtering, data refresh): 95%+
  - Business logic (MovieService, SearchService): 90%+
  - API routes: 85%+
  
- **Frontend**: 70% code coverage (Vitest)
  - Core components (MovieCard, FilterPanel): 90%+
  - Pages (SearchPage, MovieDetail): 80%+
  - Utility functions: 95%+

- **E2E**: Cover all user stories (P1-P4 acceptance scenarios)

---

## Deployment & Operations

### Weekly Data Refresh Job

**Scheduler**: Celery + Redis

**Architecture**:
```python
# app/jobs/weekly_refresh.py
from celery import Celery
from app.integrations.omdb_client import OMDbClient
from app.integrations.kim_scraper import KIMScraper

celery = Celery('tasks', broker='redis://localhost:6379/0')

@celery.task(bind=True, max_retries=3)
def refresh_movie_data(self):
    """Weekly refresh of movie data from OMDb and Kids-in-Mind"""
    try:
        # 1. Fetch new/updated movies from OMDb
        omdb_client = OMDbClient()
        movies = omdb_client.fetch_movies()
        
        # 2. Scrape content scores from Kids-in-Mind
        kim_scraper = KIMScraper()
        for movie in movies:
            content_scores = kim_scraper.scrape(movie.title, movie.year)
            movie.content_scores = content_scores
        
        # 3. Match and store in database
        save_to_database(movies)
        
        # 4. Log success
        log_refresh_success(len(movies))
        
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

**Scheduling** (Celery Beat):
```python
# celeryconfig.py
from celery.schedules import crontab

beat_schedule = {
    'weekly-refresh': {
        'task': 'app.jobs.weekly_refresh.refresh_movie_data',
        'schedule': crontab(day_of_week='sunday', hour=2, minute=0),  # Every Sunday at 2 AM
    },
}
```

**Error Handling Strategy**:
- **Retry Logic**: Max 3 retries with exponential backoff (1 min, 2 min, 4 min)
- **Partial Failure Handling**: If OMDb succeeds but Kids-in-Mind fails, store OMDb data and flag movies for content score retry
- **Keep Existing Data**: On complete failure, retain existing database records (don't delete)
- **Logging**: Structured logging to file + monitoring system (e.g., Sentry)

**Monitoring**:
```python
# app/models/data_refresh_log.py
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime

class DataRefreshLog(Base):
    __tablename__ = 'data_refresh_logs'
    
    id = Column(Integer, primary_key=True)
    refresh_date = Column(DateTime, default=datetime.utcnow)
    source = Column(String)  # 'omdb' or 'kids-in-mind'
    status = Column(String)  # 'success' or 'failed'
    records_updated = Column(Integer)
    errors = Column(JSON, nullable=True)  # Error details
    duration_seconds = Column(Integer)
```

**Monitoring Dashboard**:
- Track refresh success rate (target: >95%)
- Alert on consecutive failures (>2 in a row)
- Monitor scraping success rate (target: >90% for Kids-in-Mind)
- Track API rate limit errors (should be 0 with proper throttling)

**Alternatives Considered**:
- **Cron jobs + Python scripts**: Simpler but lacks retry logic, monitoring, and async capabilities
- **APScheduler**: Lighter than Celery but less mature for distributed task queues

---

## Session Storage Implementation

**Approach**: Browser sessionStorage API + React Context

**Why sessionStorage over localStorage**:
- **Requirement**: FR-029 specifies "session-only filter persistence" (no cross-session persistence)
- **Privacy**: Filters cleared when user closes tab (appropriate for content filtering preferences)
- **Scope**: Per-tab isolation (user can have different filter sets in multiple tabs)

**Implementation Pattern**:
```javascript
// hooks/useFilters.js
import { useState, useEffect } from 'react'

const STORAGE_KEY = 'movie-filters'

export function useFilters() {
  const [filters, setFilters] = useState(() => {
    // Initialize from sessionStorage on mount
    const stored = sessionStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : getDefaultFilters()
  })
  
  // Persist to sessionStorage on change
  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(filters))
  }, [filters])
  
  return [filters, setFilters]
}

function getDefaultFilters() {
  return {
    genres: [],
    year_min: null,
    year_max: null,
    mpaa_ratings: [],
    imdb_min: 0,
    rt_min: 0,
    metacritic_min: 0,
    sex_max: null,
    violence_max: null,
    language_max: null
  }
}
```

**URL Query Parameter Sync** (optional enhancement for sharing):
```javascript
// Sync filters with URL for shareability
import { useSearchParams } from 'react-router-dom'

export function useFiltersWithURL() {
  const [searchParams, setSearchParams] = useSearchParams()
  
  const filters = Object.fromEntries(searchParams.entries())
  
  const updateFilters = (newFilters) => {
    setSearchParams(newFilters)
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(newFilters))
  }
  
  return [filters, updateFilters]
}

// URL format: /search?genres=Action,Sci-Fi&sex_max=5&violence_max=6
```

**Browser Compatibility**: sessionStorage is supported in all modern browsers (Chrome, Firefox, Safari, Edge)

**State Serialization**:
- Store filter state as JSON string
- Parse on retrieval (handle JSON parse errors gracefully)
- Clear sessionStorage on explicit user action (e.g., "Reset Filters" button)

---

## Summary of Resolved Clarifications

| Technical Context Item | Decision |
|------------------------|----------|
| **Language/Version** | Python 3.11+ (backend), React 18+ with TypeScript (frontend) |
| **Primary Dependencies** | FastAPI, SQLAlchemy, Celery, RapidFuzz, BeautifulSoup4 (backend); React, Tailwind CSS, Axios (frontend) |
| **Storage** | PostgreSQL 15+ with GIN indexes, JSONB support, full-text search |
| **Testing** | pytest + responses + openapi-spec-validator (backend); Vitest + RTL + Playwright (frontend) |
| **Web Scraping** | BeautifulSoup4 + lxml parser with rate limiting (1 req/2s) |
| **Fuzzy Matching** | RapidFuzz hybrid approach (TokenSort + Partial Ratio), >88 auto-match threshold |
| **Database Indexing** | GIN indexes (genre, title FTS), composite indexes (mpaa_rating, year, imdb_rating), partial indexes (content scores) |
| **Weekly Refresh** | Celery + Redis with cron schedule (Sunday 2 AM), exponential backoff retry logic |
| **Session Storage** | Browser sessionStorage API + React Context, optional URL query param sync |

All "NEEDS CLARIFICATION" items from Technical Context have been resolved with specific technology choices, rationale, and implementation approaches.

---

**Next Steps**: Proceed to Phase 1 (Design & Contracts) to generate data-model.md, contracts/api.yaml, and quickstart.md based on these technology decisions.
