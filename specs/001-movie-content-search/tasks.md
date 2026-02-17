# Tasks: Movie Content-Aware Search

**Input**: Design documents from `/specs/001-movie-content-search/`  
**Prerequisites**: plan.md, spec.md (user stories), research.md (tech stack), data-model.md, contracts/api.yaml

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Note**: Tests are NOT included as the spec does not explicitly request TDD or test implementation.

## Format: `- [X] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Shared**: `shared/contracts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (backend/, frontend/, shared/, specs/)
- [X] T002 Initialize Python 3.11+ backend with FastAPI in backend/
- [X] T003 [P] Initialize React 18+ TypeScript frontend with Vite in frontend/
- [X] T004 [P] Setup Docker Compose with PostgreSQL 15+ and Redis 7+ in docker-compose.yml
- [X] T005 [P] Create backend requirements.txt with FastAPI, SQLAlchemy, Celery, httpx, BeautifulSoup4, RapidFuzz
- [X] T006 [P] Create frontend package.json with React, TypeScript, Tailwind CSS, Axios, React Router
- [X] T007 [P] Configure backend .env.example with OMDb API key, database URL, Redis URL, rate limits
- [X] T008 [P] Configure frontend .env.example with API base URL
- [X] T009 [P] Setup Alembic for database migrations in backend/alembic/
- [X] T010 [P] Initialize Tailwind CSS configuration in frontend/tailwind.config.js

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T011 Create PostgreSQL database schema with movies, content_scores, data_refresh_logs tables in backend/alembic/versions/001_initial_schema.py
- [X] T012 [P] Create SQLAlchemy base model in backend/src/database/base.py
- [X] T013 [P] Setup database session and connection pooling in backend/src/database/session.py
- [X] T014 [P] Create Movie SQLAlchemy model in backend/src/models/movie.py
- [X] T015 [P] Create ContentScore SQLAlchemy model in backend/src/models/content_score.py
- [X] T016 [P] Create DataRefreshLog SQLAlchemy model in backend/src/models/data_refresh_log.py
- [X] T017 Create database indexes (GIN for genre/title, B-tree for ratings, composite indexes) in backend/alembic/versions/002_add_indexes.py
- [X] T018 [P] Setup FastAPI application structure with CORS middleware in backend/src/main.py
- [X] T019 [P] Create error handling middleware in backend/src/api/middleware/error_handler.py
- [X] T020 [P] Create logging middleware in backend/src/api/middleware/logging.py
- [X] T021 [P] Setup React Router configuration in frontend/src/App.tsx
- [X] T022 [P] Create API client service with axios configuration in frontend/src/services/api.ts
- [X] T023 [P] Create TypeScript types from API schema in frontend/src/types/api.types.ts
- [X] T024 [P] Create useFilters hook for session storage in frontend/src/hooks/useFilters.ts
- [X] T025 [P] Setup Tailwind base styles in frontend/src/styles/index.css

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Content-Filtered Movie Browsing (Priority: P1) 🎯 MVP

**Goal**: Users can set content tolerance thresholds (sex/nudity, violence/gore, language/profanity) and only see movies within ALL specified limits. This is the core differentiator.

**Independent Test**: Set content thresholds (e.g., max violence: 5, max language: 7, sex: any), search for movies, and verify all results respect these limits. Movies without content scores should be hidden when any content filter is active.

### Implementation for User Story 1

#### Backend Implementation

- [X] T026 [P] [US1] Create Pydantic schemas for search filters in backend/src/api/schemas/search.py
- [X] T027 [P] [US1] Create Pydantic schemas for movie response in backend/src/api/schemas/movie.py
- [X] T028 [US1] Implement SearchService with content filtering logic in backend/src/services/search_service.py
- [X] T029 [US1] Implement GET /api/movies/search endpoint with content threshold filters in backend/src/api/routes/movies.py
- [X] T030 [US1] Add content filtering query logic (sex_max, violence_max, language_max) to SearchService
- [X] T031 [US1] Implement "hide movies without content scores when any filter active" logic in SearchService
- [X] T032 [US1] Add pagination support (20-30 movies per page) to search endpoint

#### Frontend Implementation

- [X] T033 [P] [US1] Create ContentBadge component with color-coded badges (green/red) in frontend/src/components/ContentBadge.tsx
- [X] T034 [P] [US1] Create FilterPanel component with content threshold sliders in frontend/src/components/FilterPanel.tsx
- [X] T035 [P] [US1] Create MovieCard component displaying poster, title, year, genre, ratings, content badges in frontend/src/components/MovieCard.tsx
- [X] T036 [US1] Create SearchPage with filter panel and results grid in frontend/src/pages/SearchPage.tsx
- [X] T037 [US1] Implement content threshold controls (0-10 sliders and "any" option) in FilterPanel
- [X] T038 [US1] Connect FilterPanel to useFilters hook for session persistence
- [X] T039 [US1] Implement search API call with content threshold parameters in SearchPage
- [X] T040 [US1] Add color-coded content badges to MovieCard (green if within threshold, red if exceeds)
- [X] T041 [US1] Implement pagination controls in SearchPage

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. Users can set content thresholds and see filtered results.

---

## Phase 4: User Story 2 - Movie Search and Discovery (Priority: P2)

**Goal**: Users can search by title and filter using traditional criteria (genre, year range, MPAA rating, quality ratings). Results display complete metadata and images.

**Independent Test**: Search "The Matrix", filter by genre "Sci-Fi" and minimum IMDb rating of 7.0, verify results show matching movies with complete metadata.

### Implementation for User Story 2

#### Backend Implementation

- [X] T042 [P] [US2] Add title full-text search to SearchService using PostgreSQL GIN index in backend/src/services/search_service.py
- [X] T043 [P] [US2] Add genre filtering (array overlap) to SearchService in backend/src/services/search_service.py
- [X] T044 [P] [US2] Add year range filtering to SearchService in backend/src/services/search_service.py
- [X] T045 [P] [US2] Add MPAA rating filtering to SearchService in backend/src/services/search_service.py
- [X] T046 [P] [US2] Add quality rating filters (IMDb, Rotten Tomatoes, Metacritic minimums) to SearchService in backend/src/services/search_service.py
- [X] T047 [P] [US2] Add awards filtering to SearchService in backend/src/services/search_service.py
- [X] T048 [US2] Implement GET /api/genres endpoint in backend/src/api/routes/metadata.py

#### Frontend Implementation

- [X] T049 [P] [US2] Create SearchBar component with title search input in frontend/src/components/SearchBar.tsx
- [X] T050 [US2] Add genre multi-select dropdown to FilterPanel in frontend/src/components/FilterPanel.tsx
- [X] T051 [US2] Add year range inputs (min/max) to FilterPanel in frontend/src/components/FilterPanel.tsx
- [X] T052 [US2] Add MPAA rating multi-select to FilterPanel in frontend/src/components/FilterPanel.tsx
- [X] T053 [US2] Add quality rating minimum sliders (IMDb, RT, Metacritic) to FilterPanel in frontend/src/components/FilterPanel.tsx
- [X] T054 [US2] Add awards filter controls to FilterPanel in frontend/src/components/FilterPanel.tsx
- [X] T055 [US2] Update MovieCard to display poster image with placeholder fallback in frontend/src/components/MovieCard.tsx
- [X] T056 [US2] Update MovieCard to display ratings from all sources (IMDb, RT, Metacritic) in frontend/src/components/MovieCard.tsx
- [X] T057 [US2] Integrate SearchBar with SearchPage API calls in frontend/src/pages/SearchPage.tsx
- [X] T058 [US2] Implement "no results" message with filter relaxation suggestions in frontend/src/pages/SearchPage.tsx

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Users can search by title and use both traditional and content filters.

---

## Phase 5: User Story 3 - Detailed Movie Information (Priority: P3)

**Goal**: Users can click a movie to view comprehensive details including full plot, complete cast, all ratings, awards, and detailed content scores with visual indicators.

**Independent Test**: Click any movie in results, verify all metadata fields are populated, content scores are visually clear, and all rating sources are displayed.

### Implementation for User Story 3

#### Backend Implementation

- [X] T059 [P] [US3] Create MovieService for retrieving single movie details in backend/src/services/movie_service.py
- [X] T060 [US3] Implement GET /api/movies/{id} endpoint in backend/src/api/routes/movies.py
- [X] T061 [US3] Add plot, awards_metadata, timestamps to movie detail response schema in backend/src/api/schemas/movie.py

#### Frontend Implementation

- [X] T062 [P] [US3] Create MovieDetail page component in frontend/src/pages/MovieDetail.tsx
- [X] T063 [US3] Add comprehensive movie information display (title, year, runtime, plot, director, cast) to MovieDetail
- [X] T064 [US3] Add all rating sources display section to MovieDetail (IMDb, RT, Metacritic with icons)
- [X] T065 [US3] Add awards information section to MovieDetail (awards summary, specific awards list)
- [X] T066 [US3] Add detailed content scores display with color-coded badges and threshold indicators to MovieDetail
- [X] T067 [US3] Implement navigation from MovieCard to MovieDetail page using React Router
- [X] T068 [US3] Add back button to return to search results in MovieDetail

**Checkpoint**: All three priority user stories (P1, P2, P3) are now independently functional. Users have full movie search and detail viewing capabilities.

---

## Phase 6: User Story 4 - Mobile-Responsive Experience (Priority: P4)

**Goal**: Users on mobile devices can perform all core functions with an interface optimized for touch and smaller screens (minimum 375px width).

**Independent Test**: Access site on mobile devices of various sizes, perform searches with content filters, verify all interactive elements are touch-friendly and no horizontal scrolling required.

### Implementation for User Story 4

- [X] T069 [P] [US4] Add mobile breakpoints to Tailwind configuration in frontend/tailwind.config.js
- [X] T070 [P] [US4] Make FilterPanel responsive with collapsible sections on mobile in frontend/src/components/FilterPanel.tsx
- [X] T071 [P] [US4] Make SearchBar responsive with appropriate font sizes on mobile in frontend/src/components/SearchBar.tsx
- [X] T072 [P] [US4] Make MovieCard responsive with vertical stacking on mobile in frontend/src/components/MovieCard.tsx
- [X] T073 [P] [US4] Make SearchPage layout responsive with filter drawer on mobile in frontend/src/pages/SearchPage.tsx
- [X] T074 [P] [US4] Make MovieDetail responsive with single column layout on mobile in frontend/src/pages/MovieDetail.tsx
- [X] T075 [P] [US4] Ensure touch targets are minimum 44x44px for all interactive elements in frontend/src/styles/index.css
- [X] T076 [US4] Add viewport meta tag for mobile scaling in frontend/index.html
- [X] T077 [US4] Test responsive design on mobile viewports (375px, 768px, 1024px)

**Checkpoint**: All four user stories are complete. The application is fully functional on both desktop and mobile devices.

---

## Phase 7: Data Integration (External APIs)

**Purpose**: Implement data ingestion from OMDb API and Kids-in-Mind scraping

- [X] T078 [P] Create OMDb API client with retry logic and rate limiting in backend/src/integrations/omdb_client.py
- [X] T079 [P] Create Kids-in-Mind scraper with BeautifulSoup4 in backend/src/integrations/kim_scraper.py
- [X] T080 [P] Implement fuzzy matching service using RapidFuzz in backend/src/services/matching_service.py
- [X] T081 Create Celery application configuration in backend/src/jobs/celery_app.py
- [X] T082 Implement weekly data refresh task (OMDb fetch + KIM scraping + fuzzy matching) in backend/src/jobs/weekly_refresh.py
- [X] T083 Add Celery Beat schedule for Sunday 2 AM refresh in backend/src/jobs/celery_app.py
- [X] T084 Create data refresh logging to DataRefreshLog table in backend/src/jobs/weekly_refresh.py
- [X] T085 [P] Create manual refresh script for development in backend/scripts/manual_refresh.py
- [X] T086 [P] Implement error handling and retry logic (exponential backoff) in OMDb client
- [X] T087 [P] Implement rate limiting (10 req/s for OMDb, 0.5 req/s for KIM) in clients
- [X] T088 Add validation for scraped content scores (0-10 range) in KIM scraper
- [X] T089 Implement manual review queue for fuzzy matches (75-88 confidence) in matching service

---

## Phase 8: Health & Monitoring

**Purpose**: Health check endpoint and operational monitoring

- [X] T090 [P] Implement GET /api/health endpoint in backend/src/api/routes/health.py
- [X] T091 [US1] Add database connectivity check to health endpoint
- [X] T092 [US1] Add last refresh timestamp to health endpoint from DataRefreshLog
- [X] T093 [P] Create seed test data script for development in backend/scripts/seed_test_data.py
- [X] T093b [P] Add query performance logging middleware that logs execution time for all database queries in backend/src/api/middleware/performance.py
- [X] T093c [P] Add slow query warning logs for any query exceeding 500ms threshold in backend/src/api/middleware/performance.py

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T094 [P] Add loading spinners for API calls in frontend/src/components/LoadingSpinner.tsx
- [X] T095 [P] Add error boundary component for React errors in frontend/src/components/ErrorBoundary.tsx
- [X] T096 [P] Implement user-friendly error messages for API failures in frontend/src/services/api.ts
- [X] T097 [P] Add "Content ratings unavailable" indicator for movies without content scores: gray badge with "N/A" text and tooltip "Content ratings not available for this movie" in frontend/src/components/MovieCard.tsx
- [X] T098 [P] Optimize query performance with query plan analysis (EXPLAIN ANALYZE) in backend/
- [X] T099 [P] Add logging for search queries and filter usage in backend/src/api/middleware/logging.py
- [X] T100 [P] Create README.md with setup instructions at repository root
- [X] T101 Validate quickstart.md setup instructions work correctly
- [X] T102 [P] Add API documentation link in frontend footer
- [X] T103 [P] Code cleanup and consistent formatting (Black for Python, Prettier for TypeScript)
- [X] T104 [P] Create placeholder movie poster image (300x450px, neutral gray with film icon) at frontend/src/assets/no-poster.png
- [X] T105 [P] Add content score legend component with tooltip labels (0=None, 3=Mild, 5=Moderate, 7=Strong, 10=Extreme) in frontend/src/components/ScoreLegend.tsx

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Data Integration (Phase 7)**: Can start after Foundational phase (parallel with user stories)
- **Health & Monitoring (Phase 8)**: Can start after Foundational phase (parallel with user stories)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1/US2 for navigation but independently testable
- **User Story 4 (P4)**: Can start after US1-US3 are complete (applies responsive design to existing components)

### Within Each User Story

- Backend models and schemas before services
- Services before endpoints
- API endpoints before frontend components that call them
- Component building blocks (ContentBadge, MovieCard) before pages (SearchPage)
- Core implementation before integration

### Parallel Opportunities

#### Setup Phase (Phase 1)
```bash
# Can run simultaneously:
T003: Initialize React frontend
T004: Setup Docker Compose
T005: Create backend requirements.txt
T006: Create frontend package.json
T007: Configure backend .env.example
T008: Configure frontend .env.example
T009: Setup Alembic
T010: Initialize Tailwind CSS
```

#### Foundational Phase (Phase 2)
```bash
# Can run simultaneously after database schema (T011):
T012: SQLAlchemy base model
T013: Database session setup
T014: Movie model
T015: ContentScore model
T016: DataRefreshLog model
T018: FastAPI application structure
T019: Error handling middleware
T020: Logging middleware
T021: React Router configuration
T022: API client service
T023: TypeScript types
T024: useFilters hook
T025: Tailwind base styles
```

#### User Story 1 (Phase 3)
```bash
# Backend models can run in parallel:
T026: Search filter schemas
T027: Movie response schemas

# Frontend components can run in parallel:
T033: ContentBadge component
T034: FilterPanel component
T035: MovieCard component
```

#### User Story 2 (Phase 4)
```bash
# Backend filters can run in parallel:
T042: Title full-text search
T043: Genre filtering
T044: Year range filtering
T045: MPAA rating filtering
T046: Quality rating filters
T047: Awards filtering
T048: GET /api/genres endpoint

# Frontend filter controls can run in parallel:
T051: Year range inputs
T052: MPAA rating multi-select
T053: Quality rating sliders
T054: Awards filter controls
T055: Poster image display
T056: Ratings display
```

#### User Story 3 (Phase 5)
```bash
# Can run in parallel:
T059: MovieService
T062: MovieDetail page component
```

#### User Story 4 (Phase 6)
```bash
# All responsive design tasks can run in parallel:
T069: Mobile breakpoints
T070: FilterPanel responsive
T071: SearchBar responsive
T072: MovieCard responsive
T073: SearchPage responsive
T074: MovieDetail responsive
T075: Touch target sizes
```

#### Data Integration (Phase 7)
```bash
# Clients can be built in parallel:
T078: OMDb API client
T079: Kids-in-Mind scraper
T080: Fuzzy matching service
T085: Manual refresh script
T086: OMDb error handling
T087: Rate limiting
T088: Content score validation
```

#### Polish Phase (Phase 9)
```bash
# Most polish tasks can run in parallel:
T094: Loading spinners
T095: Error boundary
T096: Error messages
T097: Content unavailable indicator
T098: Query optimization
T099: Logging
T100: README.md
T102: API documentation link
T103: Code formatting
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Content-Filtered Movie Browsing)
4. Complete Phase 7: Data Integration (minimal - seed database with sample movies)
5. Complete Phase 8: Health endpoint
6. **STOP and VALIDATE**: Test User Story 1 independently
7. Deploy/demo if ready

**MVP delivers**: Content-aware movie filtering (the core differentiator)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + Data Integration → Test independently → **Deploy/Demo (MVP!)** 🎯
3. Add User Story 2 → Test independently → Deploy/Demo (adds traditional search/filters)
4. Add User Story 3 → Test independently → Deploy/Demo (adds movie detail pages)
5. Add User Story 4 → Test independently → Deploy/Demo (adds mobile support)
6. Add Polish (Phase 9) → Final production release

**Each story adds value without breaking previous stories**

### Parallel Team Strategy

With multiple developers after Foundational phase completes:

**Week 1-2**: Setup + Foundational (whole team)

**Week 3-4**: Parallel development
- Developer A: User Story 1 (T026-T041) + Health endpoint (T090-T092)
- Developer B: User Story 2 (T042-T058) 
- Developer C: Data Integration (T078-T089)

**Week 5-6**: Integration and polish
- Developer A: User Story 3 (T059-T068)
- Developer B: User Story 4 (T069-T077)
- Developer C: Polish (T094-T103)

---

## Summary

- **Total Tasks**: 103
- **Task Count by User Story**:
  - Setup (Phase 1): 10 tasks
  - Foundational (Phase 2): 15 tasks (BLOCKS all user stories)
  - User Story 1 (P1): 16 tasks (MVP - content filtering)
  - User Story 2 (P2): 17 tasks (traditional search/filters)
  - User Story 3 (P3): 10 tasks (movie details)
  - User Story 4 (P4): 9 tasks (mobile responsive)
  - Data Integration (Phase 7): 12 tasks
  - Health & Monitoring (Phase 8): 4 tasks
  - Polish (Phase 9): 10 tasks

- **Parallel Opportunities**: 60+ tasks marked [P] can run in parallel within their phases
- **Independent Test Criteria**: Each user story has clear independent test criteria defined
- **Suggested MVP Scope**: Phase 1 + Phase 2 + User Story 1 + minimal Phase 7 + Phase 8 (41 tasks)

- **Format Validation**: ✅ ALL tasks follow the checklist format with checkbox, ID, optional [P] marker, [Story] label (for US phases), and file paths

---

## Notes

- [P] tasks = different files, no dependencies within that phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Tests are NOT included as spec does not explicitly request TDD approach
- Paths assume web application structure (backend/, frontend/) per plan.md
