# Data Model: Movie Content-Aware Search

**Date**: 2025-01-23  
**Status**: Complete  
**Technology**: PostgreSQL 15+ with SQLAlchemy 2.0+ ORM

---

## Entity Overview

The system manages three core entities:
1. **Movie** - Complete movie metadata from OMDb API
2. **ContentScore** - Content ratings from Kids-in-Mind (0-10 scale)
3. **DataRefreshLog** - Operational tracking for weekly data refresh jobs

---

## Entity Definitions

### 1. Movie

**Purpose**: Stores comprehensive movie metadata from OMDb API, including traditional ratings, cast, awards, and poster images.

**Table**: `movies`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `title` | VARCHAR(255) | NOT NULL | Movie title |
| `year` | INTEGER | NOT NULL, CHECK(year >= 1888 AND year <= 2100) | Release year |
| `runtime` | INTEGER | NULLABLE | Runtime in minutes |
| `genre` | VARCHAR[] | NOT NULL, DEFAULT '{}' | Array of genres (Action, Drama, etc.) |
| `mpaa_rating` | VARCHAR(10) | NULLABLE, CHECK(mpaa_rating IN ('G', 'PG', 'PG-13', 'R', 'NC-17', 'Not Rated')) | MPAA content rating |
| `plot` | TEXT | NULLABLE | Full plot summary |
| `director` | VARCHAR(255) | NULLABLE | Director name |
| `cast` | VARCHAR[] | DEFAULT '{}' | Array of primary cast members |
| `poster_url` | VARCHAR(500) | NULLABLE | URL to poster image |
| `imdb_rating` | DECIMAL(3,1) | NULLABLE, CHECK(imdb_rating >= 0 AND imdb_rating <= 10) | IMDb rating (0-10) |
| `rt_rating` | INTEGER | NULLABLE, CHECK(rt_rating >= 0 AND rt_rating <= 100) | Rotten Tomatoes percentage (0-100) |
| `metacritic_rating` | INTEGER | NULLABLE, CHECK(metacritic_rating >= 0 AND metacritic_rating <= 100) | Metacritic score (0-100) |
| `awards_summary` | TEXT | NULLABLE | Awards description (e.g., "Won 4 Oscars") |
| `awards_count` | INTEGER | DEFAULT 0 | Total number of awards won |
| `nominations_count` | INTEGER | DEFAULT 0 | Total number of nominations |
| `awards_metadata` | JSONB | NULLABLE | Detailed awards data (structured JSON) |
| `omdb_id` | VARCHAR(50) | UNIQUE, NOT NULL | OMDb API identifier (e.g., "tt0133093") |
| `source` | VARCHAR(20) | DEFAULT 'omdb' | Data source identifier |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation timestamp |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |

#### Indexes

```sql
-- Primary key
CREATE INDEX idx_movies_id ON movies (id);

-- Title full-text search (GIN index with tsvector)
CREATE INDEX idx_movies_title_fts ON movies USING GIN (to_tsvector('english', title));

-- Genre array search (GIN index)
CREATE INDEX idx_movies_genre ON movies USING GIN (genre);

-- Individual filter fields
CREATE INDEX idx_movies_year ON movies (year);
CREATE INDEX idx_movies_mpaa_rating ON movies (mpaa_rating);
CREATE INDEX idx_movies_imdb_rating ON movies (imdb_rating);
CREATE INDEX idx_movies_rt_rating ON movies (rt_rating);
CREATE INDEX idx_movies_metacritic_rating ON movies (metacritic_rating);

-- Composite index for common filter combinations
CREATE INDEX idx_movies_filters_composite ON movies (mpaa_rating, year, imdb_rating);

-- Partial index for rated movies
CREATE INDEX idx_movies_rated ON movies (imdb_rating) WHERE imdb_rating > 0;

-- Awards filtering
CREATE INDEX idx_movies_awards ON movies (awards_count, nominations_count);

-- OMDb ID for lookups
CREATE UNIQUE INDEX idx_movies_omdb_id ON movies (omdb_id);
```

#### Relationships

- **One-to-One** with `ContentScore` (via `movie_id` foreign key)
  - A movie may have zero or one content score record
  - Content scores are optional (FR-024: movies without content scores are shown when no content filters active)

#### Validation Rules

1. **Title**: Required, max 255 characters
2. **Year**: Required, range 1888-2100 (1888 = first film, 2100 = future planning)
3. **MPAA Rating**: Must be one of: 'G', 'PG', 'PG-13', 'R', 'NC-17', 'Not Rated', or NULL
4. **Ratings**: 
   - IMDb: 0.0-10.0 (one decimal place)
   - Rotten Tomatoes: 0-100 (integer percentage)
   - Metacritic: 0-100 (integer score)
5. **Genre**: Array of strings, cannot be empty if specified
6. **OMDb ID**: Required, unique, format "tt[0-9]{7,8}"

#### Example Record

```json
{
  "id": "a1b2c3d4-e5f6-4789-0abc-def123456789",
  "title": "The Matrix",
  "year": 1999,
  "runtime": 136,
  "genre": ["Action", "Sci-Fi"],
  "mpaa_rating": "R",
  "plot": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
  "director": "Lana Wachowski, Lilly Wachowski",
  "cast": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"],
  "poster_url": "https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg",
  "imdb_rating": 8.7,
  "rt_rating": 87,
  "metacritic_rating": 73,
  "awards_summary": "Won 4 Oscars. 42 wins & 51 nominations total",
  "awards_count": 42,
  "nominations_count": 51,
  "awards_metadata": {
    "oscars": ["Best Visual Effects", "Best Film Editing", "Best Sound", "Best Sound Effects Editing"],
    "bafta": ["Best Achievement in Special Visual Effects"],
    "saturn": ["Best Science Fiction Film"]
  },
  "omdb_id": "tt0133093",
  "source": "omdb",
  "created_at": "2025-01-20T10:30:00Z",
  "updated_at": "2025-01-23T02:15:00Z"
}
```

---

### 2. ContentScore

**Purpose**: Stores Kids-in-Mind content ratings for three categories: sex/nudity, violence/gore, and language/profanity (0-10 scale).

**Table**: `content_scores`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `movie_id` | UUID | FOREIGN KEY(movies.id), UNIQUE, NOT NULL | References Movie |
| `sex_nudity` | INTEGER | NOT NULL, CHECK(sex_nudity >= 0 AND sex_nudity <= 10) | Sex/nudity content level (0-10) |
| `violence_gore` | INTEGER | NOT NULL, CHECK(violence_gore >= 0 AND violence_gore <= 10) | Violence/gore content level (0-10) |
| `language_profanity` | INTEGER | NOT NULL, CHECK(language_profanity >= 0 AND language_profanity <= 10) | Language/profanity content level (0-10) |
| `source` | VARCHAR(20) | DEFAULT 'kids-in-mind' | Data source identifier |
| `source_available` | BOOLEAN | DEFAULT TRUE | Whether this movie is still available in Kids-in-Mind source |
| `scraped_at` | TIMESTAMP | DEFAULT NOW() | When content scores were scraped |
| `updated_at` | TIMESTAMP | DEFAULT NOW() | Last update timestamp |
| `match_confidence` | DECIMAL(5,2) | NULLABLE | Fuzzy matching confidence score (0-100) |
| `manually_reviewed` | BOOLEAN | DEFAULT FALSE | Whether match was manually verified |

#### Indexes

```sql
-- Primary key
CREATE INDEX idx_content_scores_id ON content_scores (id);

-- Foreign key to movies (unique, one-to-one relationship)
CREATE UNIQUE INDEX idx_content_scores_movie_id ON content_scores (movie_id);

-- Individual content score indexes (for range filtering)
CREATE INDEX idx_content_scores_sex ON content_scores (sex_nudity);
CREATE INDEX idx_content_scores_violence ON content_scores (violence_gore);
CREATE INDEX idx_content_scores_language ON content_scores (language_profanity);

-- Composite index for all three content scores (frequently filtered together)
CREATE INDEX idx_content_scores_composite ON content_scores (sex_nudity, violence_gore, language_profanity);

-- Partial index for available content scores (optimize content filtering queries)
CREATE INDEX idx_content_scores_available ON content_scores (sex_nudity, violence_gore, language_profanity)
  WHERE sex_nudity IS NOT NULL;
```

#### Relationships

- **Belongs To** `Movie` (via `movie_id` foreign key)
  - Each content score is associated with exactly one movie
  - Foreign key constraint ensures referential integrity
  - ON DELETE CASCADE: If movie is deleted, content score is also deleted

#### Validation Rules

1. **All Scores**: Required integers in range 0-10
   - 0 = minimal/no content
   - 10 = extreme content
2. **Movie ID**: Required, must reference existing movie record
3. **Source**: Default 'kids-in-mind', identifies scraping source
4. **Match Confidence**: Optional, range 0-100 (percentage)
5. **Manually Reviewed**: Boolean flag for human verification of fuzzy matches

#### Example Record

```json
{
  "id": "b2c3d4e5-f6a7-4890-1bcd-ef234567890a",
  "movie_id": "a1b2c3d4-e5f6-4789-0abc-def123456789",
  "sex_nudity": 3,
  "violence_gore": 8,
  "language_profanity": 5,
  "source": "kids-in-mind",
  "scraped_at": "2025-01-20T11:00:00Z",
  "updated_at": "2025-01-23T02:15:00Z",
  "match_confidence": 92.5,
  "manually_reviewed": false
}
```

---

### 3. DataRefreshLog

**Purpose**: Operational monitoring and auditing for weekly data refresh jobs. Tracks success/failure, performance, and errors.

**Table**: `data_refresh_logs`

#### Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY | Unique identifier |
| `refresh_date` | TIMESTAMP | NOT NULL, DEFAULT NOW() | When refresh job started |
| `source` | VARCHAR(20) | NOT NULL, CHECK(source IN ('omdb', 'kids-in-mind')) | Data source being refreshed |
| `status` | VARCHAR(20) | NOT NULL, CHECK(status IN ('success', 'failed', 'partial')) | Job outcome |
| `records_fetched` | INTEGER | DEFAULT 0 | Number of records retrieved from source |
| `records_updated` | INTEGER | DEFAULT 0 | Number of database records updated |
| `records_created` | INTEGER | DEFAULT 0 | Number of new database records created |
| `records_failed` | INTEGER | DEFAULT 0 | Number of records that failed to process |
| `errors` | JSONB | NULLABLE | Structured error details (array of error objects) |
| `duration_seconds` | INTEGER | NULLABLE | Job execution time in seconds |
| `completed_at` | TIMESTAMP | NULLABLE | When refresh job completed |

#### Indexes

```sql
-- Primary key
CREATE INDEX idx_data_refresh_logs_id ON data_refresh_logs (id);

-- Query by date range
CREATE INDEX idx_data_refresh_logs_date ON data_refresh_logs (refresh_date DESC);

-- Filter by source and status
CREATE INDEX idx_data_refresh_logs_source_status ON data_refresh_logs (source, status);

-- Performance monitoring (find slow jobs)
CREATE INDEX idx_data_refresh_logs_duration ON data_refresh_logs (duration_seconds DESC);
```

#### Validation Rules

1. **Source**: Must be 'omdb' or 'kids-in-mind'
2. **Status**: Must be 'success', 'failed', or 'partial'
   - 'success': All records processed successfully
   - 'failed': Job failed completely
   - 'partial': Some records succeeded, some failed
3. **Record Counts**: Non-negative integers
4. **Duration**: Positive integer (seconds)

#### Example Record

```json
{
  "id": "c3d4e5f6-a7b8-4901-2cde-f345678901bc",
  "refresh_date": "2025-01-23T02:00:00Z",
  "source": "kids-in-mind",
  "status": "partial",
  "records_fetched": 5000,
  "records_updated": 4850,
  "records_created": 120,
  "records_failed": 30,
  "errors": [
    {
      "movie_title": "The Matrix Reloaded",
      "error_type": "ScrapingError",
      "message": "Content scores not found on detail page",
      "timestamp": "2025-01-23T02:45:00Z"
    },
    {
      "movie_title": "Inception",
      "error_type": "TimeoutError",
      "message": "HTTP request timeout after 15 seconds",
      "timestamp": "2025-01-23T03:12:00Z"
    }
  ],
  "duration_seconds": 4320,
  "completed_at": "2025-01-23T03:12:00Z"
}
```

---

## State Transitions

### Movie Matching Workflow

Movies from OMDb must be matched to content scores from Kids-in-Mind using fuzzy matching.

**States**:
1. **unmatched** - Movie exists in database without content score
2. **pending_review** - Fuzzy match found with confidence 75-88 (needs manual verification)
3. **matched** - High confidence match (>88) or manually approved match
4. **no_content** - Confirmed to have no Kids-in-Mind content score available

**Transitions**:

```
[OMDb Movie Created]
        ↓
    unmatched
        ↓
    [Fuzzy Matching]
        ↓
    ┌───────┴────────┐
    ↓                ↓
[High Confidence]  [Low Confidence]
  (score > 88)      (75 < score < 88)
    ↓                ↓
  matched      pending_review
                     ↓
              [Manual Review]
                     ↓
              ┌──────┴──────┐
              ↓             ↓
          [Approve]     [Reject]
              ↓             ↓
          matched      no_content
```

**Implementation Note**: State is not explicitly stored in database. State is derived from:
- `unmatched`: movie exists, no content_score record
- `pending_review`: content_score exists with `match_confidence` between 75-88 and `manually_reviewed = false`
- `matched`: content_score exists with `match_confidence > 88` or `manually_reviewed = true`
- `no_content`: marker record or absence of content_score after manual review

---

### Data Refresh Job States

**States**:
1. **scheduled** - Job is queued (Celery task pending)
2. **running** - Job is currently executing
3. **completed** - Job finished successfully
4. **failed** - Job failed after retries exhausted

**Transitions**:

```
  scheduled
      ↓
  [Job Starts]
      ↓
   running
      ↓
  ┌───┴────┐
  ↓        ↓
[Success] [Error]
  ↓        ↓
completed [Retry?]
           ↓
      ┌────┴─────┐
      ↓          ↓
   [Yes]       [No]
      ↓          ↓
   running    failed
```

**Implementation**: Celery task states + DataRefreshLog records

---

## Query Patterns

### Common Queries

#### 1. Search Movies with Content Filters (Core Feature)

```sql
-- Find movies matching title search and content thresholds
SELECT m.*, cs.*
FROM movies m
LEFT JOIN content_scores cs ON m.id = cs.movie_id
WHERE 
  to_tsvector('english', m.title) @@ to_tsquery('matrix')
  AND m.genre && ARRAY['Action', 'Sci-Fi']
  AND m.year BETWEEN 1990 AND 2010
  AND m.mpaa_rating IN ('PG-13', 'R')
  AND m.imdb_rating >= 7.0
  -- Content filtering (only when thresholds set)
  AND (cs.sex_nudity <= 5 OR :sex_max IS NULL)
  AND (cs.violence_gore <= 6 OR :violence_max IS NULL)
  AND (cs.language_profanity <= 7 OR :language_max IS NULL)
  -- Hide movies without content scores when ANY content filter is active
  AND (
    (:sex_max IS NULL AND :violence_max IS NULL AND :language_max IS NULL)
    OR cs.id IS NOT NULL
  )
ORDER BY m.imdb_rating DESC
LIMIT 30 OFFSET 0;
```

**Indexes Used**:
- `idx_movies_title_fts` (full-text search on title)
- `idx_movies_genre` (GIN array index)
- `idx_movies_filters_composite` (mpaa_rating, year, imdb_rating)
- `idx_content_scores_composite` (sex_nudity, violence_gore, language_profanity)

**Performance**: <500ms for combined filters

---

#### 2. Get Movie with Content Score

```sql
-- Retrieve single movie with all details
SELECT m.*, cs.*
FROM movies m
LEFT JOIN content_scores cs ON m.id = cs.movie_id
WHERE m.id = :movie_id;
```

**Indexes Used**: `idx_movies_id` (primary key lookup)

**Performance**: <10ms

---

#### 3. Browse Movies Without Content Filters

```sql
-- Show all movies (including those without content scores)
SELECT m.*, cs.*
FROM movies m
LEFT JOIN content_scores cs ON m.id = cs.movie_id
WHERE m.genre && ARRAY['Drama']
ORDER BY m.imdb_rating DESC
LIMIT 30;
```

**Note**: LEFT JOIN ensures movies without content scores are included

---

#### 4. Manual Review Queue (Pending Matches)

```sql
-- Find movies needing manual match verification
SELECT m.title, m.year, cs.match_confidence, cs.manually_reviewed
FROM movies m
JOIN content_scores cs ON m.id = cs.movie_id
WHERE cs.match_confidence BETWEEN 75 AND 88
  AND cs.manually_reviewed = false
ORDER BY cs.match_confidence ASC
LIMIT 50;
```

**Indexes Used**: `idx_content_scores_movie_id`

---

#### 5. Refresh Job Monitoring

```sql
-- Get last 10 refresh jobs with error summaries
SELECT 
  source,
  status,
  refresh_date,
  records_updated,
  records_failed,
  duration_seconds,
  jsonb_array_length(COALESCE(errors, '[]'::jsonb)) as error_count
FROM data_refresh_logs
ORDER BY refresh_date DESC
LIMIT 10;
```

**Indexes Used**: `idx_data_refresh_logs_date`

---

## Database Schema DDL

Complete PostgreSQL schema definition:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Movies table
CREATE TABLE movies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    year INTEGER NOT NULL CHECK(year >= 1888 AND year <= 2100),
    runtime INTEGER,
    genre VARCHAR[] NOT NULL DEFAULT '{}',
    mpaa_rating VARCHAR(10) CHECK(mpaa_rating IN ('G', 'PG', 'PG-13', 'R', 'NC-17', 'Not Rated')),
    plot TEXT,
    director VARCHAR(255),
    cast VARCHAR[] DEFAULT '{}',
    poster_url VARCHAR(500),
    imdb_rating DECIMAL(3,1) CHECK(imdb_rating >= 0 AND imdb_rating <= 10),
    rt_rating INTEGER CHECK(rt_rating >= 0 AND rt_rating <= 100),
    metacritic_rating INTEGER CHECK(metacritic_rating >= 0 AND metacritic_rating <= 100),
    awards_summary TEXT,
    awards_count INTEGER DEFAULT 0,
    nominations_count INTEGER DEFAULT 0,
    awards_metadata JSONB,
    omdb_id VARCHAR(50) UNIQUE NOT NULL,
    source VARCHAR(20) DEFAULT 'omdb',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Content scores table
CREATE TABLE content_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    movie_id UUID UNIQUE NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    sex_nudity INTEGER NOT NULL CHECK(sex_nudity >= 0 AND sex_nudity <= 10),
    violence_gore INTEGER NOT NULL CHECK(violence_gore >= 0 AND violence_gore <= 10),
    language_profanity INTEGER NOT NULL CHECK(language_profanity >= 0 AND language_profanity <= 10),
    source VARCHAR(20) DEFAULT 'kids-in-mind',
    scraped_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    match_confidence DECIMAL(5,2),
    manually_reviewed BOOLEAN DEFAULT FALSE
);

-- Data refresh logs table
CREATE TABLE data_refresh_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    refresh_date TIMESTAMP NOT NULL DEFAULT NOW(),
    source VARCHAR(20) NOT NULL CHECK(source IN ('omdb', 'kids-in-mind')),
    status VARCHAR(20) NOT NULL CHECK(status IN ('success', 'failed', 'partial')),
    records_fetched INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_created INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    errors JSONB,
    duration_seconds INTEGER,
    completed_at TIMESTAMP
);

-- Indexes (see Entity Definitions sections above for complete list)

-- Trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_movies_updated_at BEFORE UPDATE ON movies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_scores_updated_at BEFORE UPDATE ON content_scores
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Data Integrity Rules

### Referential Integrity

1. **Content Score → Movie**: Foreign key constraint ensures content scores only exist for valid movies
2. **Cascade Deletion**: If movie is deleted, associated content score is automatically deleted
3. **No Orphan Content Scores**: Database constraint prevents content scores without corresponding movies

### Business Logic Integrity

1. **Content Filtering Logic** (FR-014):
   - When ANY content threshold is set (not "any"), only display movies WITH content scores
   - When ALL content thresholds are "any", display all movies (with or without content scores)
   - Implemented in application layer, not database constraints

2. **Fuzzy Matching Confidence**:
   - Auto-match threshold: >88
   - Manual review threshold: 75-88
   - Skip threshold: <75
   - Enforced in matching service, not database

3. **Weekly Refresh Idempotency**:
   - Refresh job should be idempotent (can run multiple times safely)
   - Use `omdb_id` as unique identifier for upsert operations
   - Update existing records, insert new ones, skip duplicates

---

## Migration Strategy

### Initial Schema Setup

```bash
# Apply schema migration
alembic upgrade head

# Seed initial test data (optional)
python scripts/seed_test_data.py
```

### Future Schema Changes

Use Alembic for database migrations:

```python
# Example migration: Add new index
# migrations/versions/001_add_awards_index.py

def upgrade():
    op.create_index(
        'idx_movies_awards',
        'movies',
        ['awards_count', 'nominations_count']
    )

def downgrade():
    op.drop_index('idx_movies_awards', 'movies')
```

---

## Performance Considerations

1. **Index Maintenance**: With 5,000 movies, all indexes fit in memory (~50MB). VACUUM ANALYZE weekly to update statistics.

2. **Full-Text Search**: Use `to_tsvector` with GIN index for title search. Consider adding `plot` to full-text search if needed.

3. **Array Queries**: GIN index on `genre` enables fast array overlap queries (`genre && ARRAY['Action']`).

4. **Pagination**: Use `LIMIT` and `OFFSET` for pagination. For large offsets (>1000), consider keyset pagination (cursor-based).

5. **Connection Pooling**: Use SQLAlchemy connection pool with `pool_size=5` to manage database connections efficiently.

6. **Query Caching**: Cache popular filter combinations in Redis (e.g., "Action movies with IMDb > 8.0 and violence < 6").

---

**Next Steps**: Generate API contracts (contracts/api.yaml) based on this data model.
