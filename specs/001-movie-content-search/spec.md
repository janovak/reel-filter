# Feature Specification: Movie Content-Aware Search

**Feature Branch**: `001-movie-content-search`  
**Created**: 2025-01-23  
**Status**: Draft  
**Input**: User description: "Movie Content Search — Product Specification — A website where users can search for movies and filter results not just by traditional criteria (genre, ratings, awards) but by their personal tolerance for specific types of content."

## Clarifications

### Session 2025-01-23

- Q: How should the system handle movies that exist in OMDb but have no Kids-in-Mind content scores? → A: Show movies without content scores when no content filters are active, but hide them when any content threshold is set. This means users can browse all movies when not filtering by content, but only see scored movies when using content tolerance sliders.
- Q: What is the data refresh frequency for both OMDb API and Kids-in-Mind scraping? → A: Weekly refresh. Balanced approach for both OMDb API usage and Kids-in-Mind scraping frequency.
- Q: Does the system require user accounts and authentication, or is it anonymous with no persistent user profiles? → A: No user accounts, fully anonymous search with session-only filter persistence.
- Q: Content Score Visual Representation → A: Color-coded numeric badges with threshold indicators. Green badge if within user's threshold, red if would exceed. Combines precision with quick visual scanning.
- Q: Search Results → A: Paginated results, 20-30 movies per page. Traditional approach with clear navigation.
- Q: Movie Data Matching → A: Fuzzy matching with manual review queue for low-confidence matches. Automates high-confidence matches, flags edge cases for human review.
- Q: Error Handling for Data Failures → A: Keep existing data, retry failed updates, log for monitoring. Transparent to users, operator-visible issues.
- Q: Year mismatch tolerance when matching movies between sources → A: Allow ±1 year difference. Treat as high-confidence match if title is exact and year is within 1.
- Q: How to handle changed content scores during weekly refresh → A: Overwrite silently with new values. Log old/new values in the data refresh log for auditing.
- Q: How to handle new movies discovered during weekly refresh → A: Auto-add new movies found during weekly refresh. The fuzzy matching + manual review queue already handles uncertain matches.
- Q: How to handle movies removed from Kids-in-Mind source → A: Keep movies in database even if they disappear from source. Flag as "source unavailable" in refresh log. Do not delete.
- Q: Refresh order of operations between Kids-in-Mind and OMDb → A: Scrape Kids-in-Mind first to get the movie list with content scores, then enrich each movie with OMDb metadata. Only call OMDb for movies that have content scores.
- Q: Poster image storage strategy → A: Store the OMDb poster URL directly, do not download or host images locally. Use a placeholder image for movies with missing poster URLs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Content-Filtered Movie Browsing (Priority: P1)

A user wants to find movies that match their personal content comfort levels. They set tolerance thresholds for sex/nudity, violence/gore, and profanity, then browse or search for movies. Only movies within all specified thresholds are displayed in results.

**Why this priority**: This is the core differentiator and primary value proposition. Without content filtering, the application is just another movie search site. This delivers immediate value as a standalone feature.

**Independent Test**: Can be fully tested by setting content thresholds (e.g., max violence: 5, max language: 7, sex: any), searching for movies, and verifying all results respect these limits. Delivers the unique value of finding content-appropriate movies.

**Acceptance Scenarios**:

1. **Given** a user has set maximum violence to 5, maximum language to 7, and sex to "any" (no limit), **When** they search for action movies, **Then** only movies with violence ≤5 and language ≤7 are displayed, regardless of sex/nudity scores
2. **Given** a user has set all three content thresholds, **When** they view search results, **Then** each movie displays its content scores as color-coded numeric badges (green if within threshold, red if exceeds) alongside traditional ratings
3. **Given** a movie has violence score of 8, **When** a user has set maximum violence to 6, **Then** that movie does not appear in search results
4. **Given** a user sets "any" for all three content categories, **When** they search, **Then** all movies with content scores are displayed (no content filtering applied)

---

### User Story 2 - Movie Search and Discovery (Priority: P2)

A user searches for movies by title and filters results using traditional criteria like genre, year range, MPAA rating, and quality ratings (IMDb, Rotten Tomatoes, Metacritic). Results display poster images, basic metadata, ratings, and cast information.

**Why this priority**: Essential for usability but secondary to the unique content filtering feature. Users need to find movies, but the search itself isn't the differentiator. This can function independently as a basic movie search tool.

**Independent Test**: Can be tested by searching "The Matrix", filtering by genre "Sci-Fi" and minimum IMDb rating of 7.0, and verifying results show matching movies with complete metadata and images.

**Acceptance Scenarios**:

1. **Given** a user enters "Matrix" in the search field, **When** they submit the search, **Then** all movies with "Matrix" in the title are displayed with poster, title, year, genre, and ratings
2. **Given** search results are displayed, **When** a user applies genre filter "Action" and year range 1990-2000, **Then** only action movies from that decade remain in results
3. **Given** a user sets minimum IMDb rating to 8.0, **When** viewing results, **Then** all displayed movies have IMDb rating ≥8.0
4. **Given** a user filters by "Oscar-nominated", **When** results are displayed, **Then** only movies with Oscar nominations appear with awards summary visible
5. **Given** no search term is entered, **When** a user applies only filters (genre, year, ratings), **Then** all movies matching those criteria are browsable

---

### User Story 3 - Detailed Movie Information (Priority: P3)

A user clicks on a movie from search results to view comprehensive details including full plot summary, complete cast and crew, all rating sources, awards information, and detailed content scores with visual indicators.

**Why this priority**: Provides depth and helps users make informed decisions, but the core value (finding appropriate movies) is already delivered by P1 and P2. This enhances the experience but isn't essential for MVP functionality.

**Independent Test**: Can be tested by clicking any movie in results and verifying all metadata fields are populated, content scores are visually clear, and all three rating sources are displayed.

**Acceptance Scenarios**:

1. **Given** a user is viewing search results, **When** they click on a movie, **Then** a detail view opens showing title, year, runtime, genre, MPAA rating, plot summary, director, cast, poster image, and all available ratings
2. **Given** a movie detail view is open, **When** the user views content scores, **Then** sex/nudity, violence/gore, and language/profanity scores are displayed as color-coded numeric badges with threshold indicators (green if within user's threshold, red if would exceed)
3. **Given** a movie has IMDb, Rotten Tomatoes, and Metacritic ratings, **When** viewing the detail page, **Then** all three rating sources are visible with their respective scores
4. **Given** a movie has awards information, **When** viewing details, **Then** awards summary (nominations, wins, specific awards) is displayed

---

### User Story 4 - Mobile-Responsive Experience (Priority: P4)

A user accesses the movie search site on their mobile device (phone or tablet) and can perform all core functions (search, filter, set content thresholds, view details) with an interface optimized for touch and smaller screens.

**Why this priority**: Important for accessibility and real-world usage (parents checking on-the-go, browsing while relaxing), but the core functionality must work on desktop first. This is an enhancement to reach broader audience.

**Independent Test**: Can be tested by accessing the site on mobile devices of various sizes, performing searches with content filters, and verifying all interactive elements are touch-friendly and content is readable without horizontal scrolling.

**Acceptance Scenarios**:

1. **Given** a user accesses the site on a mobile phone, **When** they view the interface, **Then** all elements scale appropriately with no horizontal scrolling required
2. **Given** a user on a tablet sets content thresholds, **When** they interact with the controls, **Then** sliders and buttons are appropriately sized for touch input (minimum 44x44px touch targets)
3. **Given** a mobile user views search results, **When** the page loads, **Then** poster images scale appropriately and movie cards stack vertically for easy scrolling

---

### Edge Cases

- When a movie exists in OMDb but has no Kids-in-Mind content scores: Show the movie with a "Content ratings unavailable" indicator when no content filters are active. Hide the movie from results when any content threshold is set (not "any"). This allows browsing the full catalog when not filtering by content, while ensuring content filtering only includes movies with known scores.
- How does the system handle movies with identical titles but different years? Results must clearly distinguish them and match correctly to content scores. During data matching, movies with exact title match and year within ±1 are treated as high-confidence matches.
- What if Kids-in-Mind has a movie that OMDb doesn't recognize? The movie cannot be displayed (requires both data sources for complete information).
- What happens when a user sets all three content thresholds to 0? Only movies with all three content scores at 0 are shown (extremely restrictive, likely very few results).
- How does the system handle network failures when fetching movie data during weekly refresh? Keep existing data, retry failed updates, and log failures for monitoring. Failures are transparent to users but operator-visible for investigation.
- What if a search or filter combination yields zero results? Display clear "No movies match your criteria" message with suggestions to relax filters.
- How are movies with missing poster images displayed? Show a local placeholder image (300×450px neutral gray with film icon) to maintain layout consistency. Poster URLs from OMDb are stored directly without local download or hosting.
- What happens when OMDb API rate limits are exceeded during live search? Queue requests appropriately or display cached results with indicator that live data may be stale.
- What happens to content scores when they change during weekly refresh? See FR-026b.
- What happens to movies that disappear from Kids-in-Mind source? See FR-026c.

## Requirements *(mandatory)*

### Functional Requirements

#### Search and Discovery
- **FR-001**: System MUST allow users to search movies by title (partial or complete matches)
- **FR-002**: System MUST filter movies by genre (single or multiple genres)
- **FR-003**: System MUST filter movies by year range or decade
- **FR-004**: System MUST filter movies by MPAA rating (G, PG, PG-13, R, NC-17, Not Rated)
- **FR-005**: System MUST filter movies by minimum quality ratings (IMDb, Rotten Tomatoes, Metacritic) independently
- **FR-006**: System MUST filter movies by awards status (Oscar-nominated, Golden Globe winner, minimum award count)
- **FR-007**: System MUST display search results with poster image, title, year, genre, primary ratings, and cast summary
- **FR-008**: System MUST support browsing all movies when no search term is provided
- **FR-009**: System MUST paginate search results, displaying 20-30 movies per page with clear navigation controls

#### Content Filtering (Core Differentiator)
- **FR-010**: System MUST provide three independent content tolerance controls: Sex/Nudity, Violence/Gore, Language/Profanity
- **FR-011**: Each content control MUST allow values from 0-10 or "any" (no limit)
- **FR-012**: System MUST filter out movies that exceed ANY of the user's set content thresholds
- **FR-013**: System MUST display content scores as color-coded numeric badges (green if within user's threshold, red if would exceed) on every movie in search results that have them
- **FR-014**: System MUST only display movies that have content scores from Kids-in-Mind when any content filter is active (not set to "any")
- **FR-015**: System MUST allow users to set "any" for categories they don't want to filter
- **FR-016**: When all content thresholds are set to "any", system MUST display all movies regardless of whether they have content scores

#### Movie Details
- **FR-017**: System MUST display comprehensive movie details when user selects a movie: title, year, runtime, genre, MPAA rating, plot summary, director, primary cast members, poster image
- **FR-018**: System MUST display all available rating sources (IMDb, Rotten Tomatoes, Metacritic) in detail view
- **FR-019**: System MUST display awards information when available (specific awards, nomination counts, win counts)
- **FR-020**: System MUST display content scores as color-coded numeric badges with threshold indicators (green if within user's threshold, red if would exceed) in detail view

#### Data Management
- **FR-021**: System MUST combine data from OMDb API (movie metadata) and Kids-in-Mind (content scores)
- **FR-022**: System MUST match movies between OMDb and Kids-in-Mind using fuzzy matching on title with ±1 year tolerance (exact title + year within 1 = high-confidence match), with a manual review queue for low-confidence matches (automate high-confidence matches, flag edge cases for human review)
- **FR-023**: System MUST store approximately 5,000 movies with both metadata and content scores
- **FR-024**: System MUST handle cases where movie exists in OMDb but not in Kids-in-Mind by showing these movies when no content filters are active, and hiding them when any content threshold is set (i.e., display with "Content ratings unavailable" indicator only when browsing without content filters)
- **FR-025**: System MUST persist movie data in a searchable database
- **FR-026**: System MUST refresh movie data on a weekly schedule by first scraping Kids-in-Mind to get the movie list with content scores, then enriching each movie with OMDb metadata (only calling OMDb for movies that have content scores)
- **FR-026a**: During weekly refresh, system MUST auto-add new movies discovered in Kids-in-Mind source (subject to fuzzy matching + manual review queue for uncertain matches)
- **FR-026b**: During weekly refresh, system MUST overwrite content scores with new values when they change, logging old/new values in the data refresh log for auditing
- **FR-026c**: System MUST retain movies in the database even if they disappear from Kids-in-Mind source, flagging them as "source unavailable" in the refresh log without deletion
- **FR-027**: When data refresh fails for any source, system MUST keep existing data, retry failed updates, and log failures for monitoring (transparent to users, operator-visible issues)

#### User Experience
- **FR-028**: System MUST provide responsive interface that works on desktop and mobile browsers
- **FR-029**: System MUST maintain user's filter and threshold settings during a browsing session using client-side session storage only (no user accounts or server-side persistence)
- **FR-030**: System MUST operate fully anonymously with no user registration, login, or profile creation
- **FR-031**: System MUST display clear feedback when no movies match search and filter criteria
- **FR-032**: System MUST handle missing poster images with placeholder graphics (poster URLs are stored directly from OMDb without local download or hosting)
- **FR-033**: System MUST display meaningful error messages when data sources are unavailable

### Key Entities *(include if feature involves data)*

- **Movie**: Represents a film with comprehensive metadata including title, release year, genre(s), MPAA rating, runtime, plot summary, director, cast members, poster image URL (stored directly from OMDb without local hosting), awards information, and quality ratings from multiple sources (IMDb score, Rotten Tomatoes percentage, Metacritic score). May include a "source unavailable" flag if the movie no longer exists in Kids-in-Mind source during refresh.

- **Content Scores**: Represents Kids-in-Mind content ratings for a movie with three numeric values (0-10 scale): sex/nudity level, violence/gore level, and language/profanity level. Each score quantifies the intensity of that content type.

- **Search Filters**: Represents user-defined criteria including text search term, genre selections, year range, MPAA rating selections, minimum quality rating thresholds (per rating source), and awards criteria

- **Content Thresholds**: Represents user-defined maximum acceptable levels for the three content categories (sex/nudity, violence/gore, language/profanity). Each threshold can be set to 0-10 or "any" (unlimited)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can find movies matching both traditional filters (genre, year, rating) and content thresholds in under 30 seconds from landing page
- **SC-002**: Content scores are visible as color-coded badges on every movie result without requiring additional clicks or interactions
- **SC-003**: 95% of searches with active content filters return only movies within all specified thresholds (5% margin for data inconsistencies)
- **SC-004**: System displays complete metadata (poster, title, year, genre, ratings, cast) for at least 90% of movies in the database
- **SC-005**: Content threshold controls respond to user input within 500 milliseconds, with results updating accordingly
- **SC-006**: Movie detail view loads complete information within 2 seconds on standard broadband connection
- **SC-007**: Mobile users can set content thresholds and perform searches without horizontal scrolling or zooming on devices with minimum 375px width
- **SC-008**: System successfully matches at least 90% of Kids-in-Mind movies to corresponding OMDb records using fuzzy matching, with low-confidence matches queued for manual review
- **SC-009**: Search results display 20-30 movies per page with pagination controls, maintaining performance across the full catalog
- **SC-010**: Search results remain accurate when combining up to 5 simultaneous filters (e.g., genre + year + 3 content thresholds)
- **SC-011**: Users can distinguish between movies with similar titles through year and additional metadata visible in search results
- **SC-012**: System handles the complete catalog of approximately 5,000 movies without performance degradation in search or filtering operations

### Assumptions

- OMDb API provides reliable and consistent data formatting for all required fields
- Kids-in-Mind website structure remains stable for web scraping purposes
- Title and year matching between OMDb and Kids-in-Mind achieves high accuracy (>90%)
- Standard web hosting infrastructure supports approximately 5,000 movie records with acceptable performance
- Users have JavaScript enabled in their browsers
- Primary user base accesses site via modern browsers (released within last 3 years)
- Content scores from Kids-in-Mind are sufficiently current (no requirement to cross-reference scores from multiple sources)
- The 0-10 numeric scale for content is self-explanatory or will have minimal legend/help text
- Users understand that absence of content scores means the movie cannot be filtered by content criteria
- Users accept that filter preferences are lost when closing the browser or clearing session storage (no cross-device or persistent preference storage)
- No requirement for user-specific features like watchlists, favorites, viewing history, or personalized recommendations
