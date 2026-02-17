# Implementation Plan: Movie Content-Aware Search

**Branch**: `001-movie-content-search` | **Date**: 2025-01-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-movie-content-search/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a web application that enables users to search and filter movies based on both traditional criteria (genre, ratings, year, awards) and granular content tolerance thresholds (sex/nudity, violence/gore, language/profanity on a 0-10 scale). The system combines data from OMDb API for movie metadata and Kids-in-Mind for content scores, storing approximately 5,000 movies in a searchable database with weekly automated refresh. Users can set content thresholds, and only movies within all specified limits are displayed. The application operates anonymously with session-only filter persistence and provides a mobile-responsive interface.

## Technical Context

**Language/Version**: Python 3.11+ (backend), React 18+ with TypeScript (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0+, BeautifulSoup4, RapidFuzz, Celery, Redis, Axios, Tailwind CSS  
**Storage**: PostgreSQL 15+ with GIN indexes for full-text search and array filtering  
**Testing**: pytest + responses (backend), Vitest + React Testing Library + Playwright (frontend)  
**Target Platform**: Web application (modern browsers: Chrome, Firefox, Safari, Edge released within last 3 years)  
**Project Type**: Web application (frontend + backend)  
**Performance Goals**: Search results in <1s, filter updates in <500ms, detail view loads in <2s, pagination supports 20-30 movies/page across 5,000 movie catalog  
**Constraints**: API rate limits (OMDb API), web scraping reliability (Kids-in-Mind structure stability), fuzzy matching accuracy >90% for movie pairing, mobile responsive (375px minimum width), no horizontal scrolling on mobile  
**Scale/Scope**: ~5,000 movies in database, weekly automated data refresh, anonymous users (no authentication), session-only state persistence, 3 content filters + 6 traditional filters, 20-30 results per page

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: User-Centric Content Filtering

**Requirement**: Every filtering feature MUST respect user-defined tolerance thresholds (0-10 scale)

- ✅ **PASS**: FR-010 through FR-016 define three independent content controls (Sex/Nudity, Violence/Gore, Language/Profanity) with 0-10 or "any" values
- ✅ **PASS**: FR-012 ensures movies exceeding ANY threshold are filtered out
- ✅ **PASS**: FR-013 and FR-020 require color-coded badges (green/red) for clear threshold communication
- ✅ **PASS**: FR-011 allows multi-criteria filtering (genre, ratings, awards, content scores)
- ✅ **PASS**: SC-003 validates 95% accuracy in filtering results

**Status**: ✅ No violations. Feature spec aligns with user-centric content filtering principle.

### Principle II: API Resilience & Data Integrity

**Requirement**: External data dependencies (OMDb API, Kids-in-Mind) MUST be treated as fallible

- ✅ **PASS**: FR-027 explicitly requires keeping existing data on refresh failures, retry logic, and failure logging
- ✅ **PASS**: FR-033 requires meaningful error messages when data sources are unavailable
- ✅ **PASS**: Edge cases document handling of network failures (keep existing data, retry, log)
- ✅ **PASS**: Research.md specifies exponential backoff retry (2s, 4s, 8s), 10s OMDb timeout, 15s KIM timeout
- ✅ **PASS**: Data validation via PostgreSQL CHECK constraints and SQLAlchemy model validation

**Status**: ✅ No violations. Core resilience requirements and implementation details fully specified.

### Principle III: Performance & Responsiveness

**Requirement**: Search/filtering operations MUST complete in under 1 second

- ✅ **PASS**: SC-001 requires finding movies in <30s from landing page (search itself should be faster)
- ✅ **PASS**: SC-005 requires content threshold controls respond in <500ms
- ✅ **PASS**: SC-006 requires detail view loads in <2s
- ✅ **PASS**: Data model defines 10+ indexes (GIN for title FTS, GIN for genre arrays, B-tree for ratings, composite for common filter combos)
- ✅ **PASS**: Research.md documents query optimization with EXPLAIN ANALYZE guidance

**Status**: ✅ No violations. Performance targets and optimization strategy fully specified.

**Overall Gate Status**: ✅ **PASS** - No constitutional violations. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/              # Data models (Movie, ContentScore, SearchFilters)
│   ├── services/            # Business logic (MovieService, SearchService)
│   ├── api/                 # REST API endpoints
│   │   ├── routes/          # Route handlers (search, movies, filters)
│   │   └── middleware/      # Error handling, logging
│   ├── integrations/        # External API clients
│   │   ├── omdb_client.py   # OMDb API wrapper
│   │   └── kim_scraper.py   # Kids-in-Mind scraper
│   ├── database/            # Database setup and migrations
│   │   ├── models.py        # SQLAlchemy/ORM models
│   │   └── migrations/      # Schema migrations
│   └── jobs/                # Scheduled tasks (weekly refresh)
└── tests/
    ├── contract/            # API contract tests
    ├── integration/         # Integration tests (API + DB)
    └── unit/                # Unit tests

frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── MovieCard.jsx    # Movie display in results
│   │   ├── ContentBadge.jsx # Color-coded content score badges
│   │   ├── FilterPanel.jsx  # Filter controls
│   │   └── SearchBar.jsx    # Search input
│   ├── pages/               # Page components
│   │   ├── SearchPage.jsx   # Main search/results page
│   │   └── MovieDetail.jsx  # Detailed movie view
│   ├── services/            # API client services
│   │   └── api.js           # Backend API calls
│   ├── hooks/               # Custom React hooks
│   │   └── useFilters.js    # Session storage for filter state
│   └── styles/              # CSS/styling
└── tests/
    ├── components/          # Component tests
    └── integration/         # E2E tests

shared/
└── contracts/               # API contracts (OpenAPI spec)
    └── api.yaml             # REST API contract

scripts/
└── data-refresh.sh          # Weekly data refresh job
```

**Structure Decision**: Web application architecture selected based on "frontend + backend" requirements. Backend handles data ingestion (OMDb API, Kids-in-Mind scraping), database operations, and search/filter logic. Frontend provides responsive UI with session-based filter persistence. Shared contracts directory ensures API consistency between frontend and backend.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations identified. This section intentionally left empty.

---

## Phase 0: Research & Technology Selection

**Goal**: Resolve all "NEEDS CLARIFICATION" items from Technical Context and establish technology stack with best practices.

### Research Tasks

1. **Backend Language/Framework Selection**
   - **Unknown**: Python vs Node.js for backend
   - **Research Focus**: 
     - Evaluate Python (FastAPI/Flask) vs Node.js (Express/NestJS) for REST API development
     - Consider web scraping capabilities (Python: BeautifulSoup/Scrapy, Node: Cheerio/Puppeteer)
     - Database ORM maturity (SQLAlchemy vs Sequelize/TypeORM)
     - Async task scheduling for weekly refresh (Celery vs node-cron/Bull)
   - **Decision Criteria**: Web scraping library quality, async job scheduling, team familiarity, deployment simplicity

2. **Frontend Framework Selection**
   - **Unknown**: Frontend framework choice
   - **Research Focus**:
     - React vs Vue vs Svelte for component-based UI
     - State management for filter persistence (Context API, Zustand, Pinia)
     - CSS framework for responsive design (Tailwind, Bootstrap, Material-UI)
   - **Decision Criteria**: Mobile responsiveness features, session storage integration, component reusability

3. **Database Technology**
   - **Unknown**: PostgreSQL vs SQLite vs MySQL
   - **Research Focus**:
     - Full-text search capabilities for movie titles/plots
     - Index performance on 5,000 movies with multiple filter fields
     - JSON field support for awards/ratings metadata
     - Deployment and hosting requirements
   - **Decision Criteria**: Search performance, indexing strategy, hosting complexity for ~5k records

4. **OMDb API Integration Best Practices**
   - **Unknown**: Rate limiting strategy, error handling patterns
   - **Research Focus**:
     - OMDb API rate limits and pricing tiers
     - Retry/backoff strategies for failed requests
     - Caching strategy for API responses
     - Bulk data fetching vs on-demand requests
   - **Decision Criteria**: Cost efficiency, resilience, refresh performance

5. **Kids-in-Mind Web Scraping Architecture**
   - **Unknown**: Scraping library, anti-scraping countermeasures, data extraction patterns
   - **Research Focus**:
     - HTML parsing libraries (BeautifulSoup, lxml, Cheerio)
     - Handling dynamic content (Puppeteer/Playwright if JavaScript-rendered)
     - Rate limiting to avoid IP blocking
     - Data validation for extracted content scores
   - **Decision Criteria**: Scraping reliability, maintainability when site changes, ethical scraping practices

6. **Fuzzy Matching Algorithm**
   - **Unknown**: Algorithm for matching movie titles between OMDb and Kids-in-Mind
   - **Research Focus**:
     - String similarity algorithms (Levenshtein distance, Jaro-Winkler, cosine similarity)
     - Libraries: fuzzywuzzy/RapidFuzz (Python), fuse.js (JavaScript)
     - Handling year mismatches, subtitle variations, foreign titles
     - Threshold tuning for >90% accuracy with manual review queue
   - **Decision Criteria**: Accuracy rate, performance on 5k movies, false positive/negative balance

7. **Database Query Optimization**
   - **Unknown**: Indexing strategy for multi-field filtering
   - **Research Focus**:
     - Composite indexes for frequently combined filters (genre + year + content scores)
     - Full-text search indexes for title searches
     - Query plan optimization for paginated results
     - Impact of 9 simultaneous filters on query performance
   - **Decision Criteria**: Query execution time <1s, index storage overhead, maintenance complexity

8. **Testing Framework Stack**
   - **Unknown**: Unit, integration, and contract testing tools
   - **Research Focus**:
     - Backend: pytest/unittest (Python) vs Jest/Mocha (Node.js)
     - Frontend: Jest + React Testing Library vs Vitest
     - API mocking: responses/httpretty (Python) vs nock/msw (Node.js)
     - Contract testing: Pact vs OpenAPI validation
     - E2E: Playwright vs Cypress
   - **Decision Criteria**: Test execution speed, mocking capabilities, contract enforcement

9. **Session Storage Implementation**
   - **Unknown**: Best practices for client-side filter persistence
   - **Research Focus**:
     - sessionStorage vs localStorage API usage
     - State serialization/deserialization patterns
     - Syncing session state with URL query parameters for shareability
   - **Decision Criteria**: Browser compatibility, state sync reliability, URL length limits

10. **Weekly Data Refresh Scheduling**
    - **Unknown**: Job scheduling mechanism for automated refresh
    - **Research Focus**:
      - Cron jobs vs task queues (Celery, Bull, Agenda)
      - Error handling and retry logic for failed API/scraping jobs
      - Logging and monitoring for refresh operations
      - Partial update strategies (update only changed movies)
    - **Decision Criteria**: Reliability, error visibility, maintenance overhead

### Output: research.md

Document structured as:

```markdown
# Research Findings: Movie Content Search

## Technology Stack

### Backend
- **Decision**: [Chosen language/framework]
- **Rationale**: [Why chosen based on criteria]
- **Alternatives Considered**: [What else was evaluated]

### Frontend
- **Decision**: [Chosen framework]
- **Rationale**: [Why chosen]
- **Alternatives Considered**: [Other options]

### Database
- **Decision**: [Chosen database]
- **Rationale**: [Performance, search capabilities]
- **Alternatives Considered**: [Comparison results]

## Integration Patterns

### OMDb API Best Practices
- **Rate Limiting**: [Strategy]
- **Error Handling**: [Retry/backoff pattern]
- **Caching**: [Approach]

### Kids-in-Mind Scraping
- **Library**: [Chosen tool]
- **Anti-Scraping Measures**: [How to handle]
- **Data Validation**: [Approach]

### Fuzzy Matching
- **Algorithm**: [Selected approach]
- **Accuracy Target**: >90%
- **Manual Review Threshold**: [Score cutoff]

## Performance Optimizations

### Database Indexing Strategy
- **Indexes**: [List of indexes for filtered fields]
- **Query Optimization**: [Approach]

### Testing Strategy
- **Unit Tests**: [Framework]
- **Integration Tests**: [Framework]
- **Contract Tests**: [Tool]
- **E2E Tests**: [Tool]

## Deployment & Operations

### Weekly Refresh Job
- **Scheduler**: [Chosen tool]
- **Error Handling**: [Strategy]
- **Monitoring**: [Approach]
```

---

## Phase 1: Design & Contracts

**Prerequisites**: research.md completed with all technology choices finalized

### Design Artifacts

#### 1. Data Model (`data-model.md`)

Extract entities from feature spec and research findings:

**Entities**:

- **Movie**
  - Fields: id, title, year, runtime, genre[], mpaa_rating, plot, director, cast[], poster_url, imdb_rating, rt_rating, metacritic_rating, awards_summary, awards_count, created_at, updated_at
  - Relationships: one-to-one with ContentScore
  - Validation: title required, year 1888-present, MPAA rating from enum, ratings 0-100 range
  - Indexes: title (full-text), year, genre (array), mpaa_rating, imdb_rating, rt_rating, metacritic_rating

- **ContentScore**
  - Fields: id, movie_id (FK), sex_nudity (0-10), violence_gore (0-10), language_profanity (0-10), source, scraped_at, updated_at
  - Relationships: belongs to Movie
  - Validation: scores 0-10 range, source = 'kids-in-mind'
  - Indexes: movie_id (unique), sex_nudity, violence_gore, language_profanity

- **DataRefreshLog**
  - Fields: id, refresh_date, source ('omdb' or 'kids-in-mind'), status ('success' or 'failed'), records_updated, errors, duration_seconds
  - Purpose: Operational monitoring for weekly refresh jobs
  - Validation: status from enum, source from enum

**State Transitions** (if applicable):
- Movie matching state: unmatched → pending_review → matched → published
- Refresh job state: scheduled → running → completed/failed

#### 2. API Contracts (`contracts/api.yaml`)

Generate OpenAPI 3.0 specification from functional requirements:

**Endpoints**:

- `GET /api/movies/search`
  - Query params: q (title search), genres[], year_min, year_max, mpaa_ratings[], imdb_min, rt_min, metacritic_min, awards_min, sex_max, violence_max, language_max, page, per_page
  - Response: { movies: [Movie], pagination: { page, per_page, total, has_next } }
  - Maps to: FR-001 to FR-016

- `GET /api/movies/{id}`
  - Response: Movie with ContentScore
  - Maps to: FR-017 to FR-020

- `GET /api/genres`
  - Response: { genres: [string] }
  - Purpose: Populate genre filter dropdown

- `GET /api/health`
  - Response: { status, database, last_refresh }
  - Purpose: Monitoring

**Error Responses**:
- 400: Invalid query parameters
- 404: Movie not found
- 500: Internal server error with user-friendly message (FR-033)

#### 3. Quickstart Guide (`quickstart.md`)

Developer setup and usage instructions:

```markdown
# Reel-Filter Quickstart

## Prerequisites
- [Language/version from research.md]
- [Database from research.md]
- [Package manager]

## Setup

1. Clone repository
2. Install dependencies
3. Configure environment variables (OMDb API key, database URL)
4. Run database migrations
5. Seed initial data (optional test dataset)

## Development

- Start backend: [command]
- Start frontend: [command]
- Run tests: [command]
- Run weekly refresh manually: [command]

## Architecture Overview

[Diagram: Frontend → Backend API → Database]
                        ↓
                   External APIs (OMDb, Kids-in-Mind)

## Key Files

- Backend entry: backend/src/main.[ext]
- Frontend entry: frontend/src/App.[ext]
- Database models: backend/src/database/models.[ext]
- API routes: backend/src/api/routes/
```

#### 4. Agent Context Update

Run `.specify/scripts/powershell/update-agent-context.ps1 -AgentType copilot` to:
- Add chosen backend framework to technology context
- Add chosen frontend framework
- Add database technology
- Add web scraping library
- Add fuzzy matching library
- Preserve manual additions between markers

### Outputs

- ✅ `data-model.md` with entities, fields, relationships, validation rules, indexes
- ✅ `contracts/api.yaml` with complete OpenAPI spec
- ✅ `quickstart.md` with developer setup instructions
- ✅ Updated agent-specific context file (`.github/copilot-instructions.md` or similar)

---

## Phase 2: Task Generation

**Status**: NOT EXECUTED BY THIS COMMAND

Task breakdown will be generated by running `/speckit.tasks` command separately, which will:
1. Read this plan.md and all Phase 1 artifacts
2. Generate dependency-ordered tasks in `tasks.md`
3. Break down implementation into atomic, testable tasks

---

## Post-Phase 1 Constitution Re-Check

**Status**: ✅ COMPLETE - All constitutional principles satisfied by design artifacts.

### Re-evaluate Principle II: API Resilience & Data Integrity

**Requirement**: External data dependencies (OMDb API, Kids-in-Mind) MUST be treated as fallible

✅ **PASS - data-model.md verification**:
- Validation rules defined for all entities (Movie, ContentScore, DataRefreshLog)
- CHECK constraints on ratings ranges (0-10, 0-100)
- Data types enforce structure (UUID, VARCHAR with length limits, ENUM for status)
- JSONB for flexible metadata with validation at application layer
- Foreign key constraints prevent orphan content scores

✅ **PASS - contracts/api.yaml verification**:
- Error response schemas defined (400, 404, 500, 503)
- Error objects include `error`, `message`, and optional `details` fields
- User-friendly error messages documented (FR-033 requirement)
- Health endpoint includes database connectivity status
- Rate limit errors documented (429 status code pattern in research.md)

✅ **PASS - quickstart.md verification**:
- Environment variables document timeout configurations (httpx timeout=10.0, KIM timeout=15.0)
- Retry logic documented in research.md (exponential backoff pattern)
- Celery retry configuration for weekly refresh (max_retries=3)
- Rate limiting documented for both OMDb (10 req/s) and Kids-in-Mind (0.5 req/s)
- Graceful degradation strategies documented (keep existing data on failure)

✅ **PASS - research.md implementation details**:
- Tenacity retry decorator with exponential backoff (2s, 4s, 8s delays)
- API timeout handling specified (10s for OMDb, 15s for Kids-in-Mind)
- Data validation functions for content scores (validate_content_score)
- Error logging and monitoring strategy (DataRefreshLog table)

**Principle II Status**: ✅ **FULLY SATISFIED**

---

### Re-evaluate Principle III: Performance & Responsiveness

**Requirement**: Search/filtering operations MUST complete in under 1 second

✅ **PASS - data-model.md index verification**:
- **Full-text search**: GIN index on `title` with tsvector (fast phrase matching)
- **Genre filtering**: GIN array index on `genre` field
- **Individual filters**: B-tree indexes on `year`, `mpaa_rating`, `imdb_rating`, `rt_rating`, `metacritic_rating`
- **Content scores**: Composite index on `(sex_nudity, violence_gore, language_profanity)`
- **Composite indexes**: `(mpaa_rating, year, imdb_rating)` for common filter combinations
- **Partial indexes**: Content-filtered queries optimized with WHERE clauses
- **Foreign keys**: Unique index on `movie_id` in content_scores for fast joins

✅ **PASS - query optimization documented**:
- Query patterns documented in data-model.md with EXPLAIN ANALYZE guidance
- Connection pooling specified (SQLAlchemy pool_size=5)
- Pagination with LIMIT/OFFSET (20-30 movies per page)
- All indexes fit in memory at 5,000 records (~50MB)
- LEFT JOIN strategy for optional content scores

✅ **PASS - pagination design**:
- API contract specifies pagination parameters (`page`, `per_page`)
- Response includes pagination metadata (total, total_pages, has_next, has_prev)
- Default 30 items per page (configurable 1-100)
- Keyset pagination suggested for large offsets (>1000) in data-model.md
- Efficient at 5,000 movies scale

✅ **PASS - performance targets documented**:
- Search results: <1s (constitution requirement met)
- Filter updates: <500ms (exceeds constitution requirement of <1s)
- Detail view: <2s (reasonable for single record lookup)
- Query examples show expected performance (<500ms for combined filters)
- Database connection pooling configured

**Principle III Status**: ✅ **FULLY SATISFIED**

---

### Overall Post-Phase 1 Assessment

**Constitution Compliance**: ✅ **100% SATISFIED**

All three constitutional principles are fully addressed by the Phase 1 design artifacts:

1. ✅ **User-Centric Content Filtering**: Data model and API contracts support all filtering requirements (FR-010 through FR-016)

2. ✅ **API Resilience & Data Integrity**: 
   - Validation rules in data-model.md
   - Error schemas in contracts/api.yaml
   - Retry/timeout configs in quickstart.md + research.md
   - Graceful degradation strategies documented

3. ✅ **Performance & Responsiveness**: 
   - Comprehensive indexing strategy (10+ indexes)
   - Query optimization patterns documented
   - Pagination design validated
   - <1s search target achievable with current design

**Design Artifacts Status**:
- ✅ research.md: 10 research tasks completed
- ✅ data-model.md: 3 entities, complete schema, indexes, validation
- ✅ contracts/api.yaml: 4 endpoints, OpenAPI 3.0 spec
- ✅ quickstart.md: Complete setup guide with troubleshooting
- ✅ copilot-instructions.md: Updated with technology stack

**Ready for Phase 2**: ✅ YES - Proceed to task generation with `/speckit.tasks` command
