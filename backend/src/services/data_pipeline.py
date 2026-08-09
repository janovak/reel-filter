"""Shared data pipeline logic for Kids-in-Mind scraping and OMDb enrichment.

Single source of truth used by both the manual CLI (scripts/manual_refresh.py)
and the scheduled Celery tasks (src/jobs/weekly_refresh.py), so the two paths
can't drift apart. Both callers get DataRefreshLog entries written for them,
which is what /api/health's last_refresh field reads from.
"""
import re
import time
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError

from src.database.session import SessionLocal
from src.models.movie import Movie
from src.models.content_score import ContentScore
from src.models.data_refresh_log import DataRefreshLog

logger = logging.getLogger(__name__)

# Kept in sync with the check_mpaa_rating constraint in src/models/movie.py.
# KIM covers TV movies/specials as well as theatrical releases, so both MPAA
# and TV Parental Guidelines ratings show up in the scrape. Keyed by the
# uppercased form so lookups are case-insensitive; values are the exact
# strings the DB constraint allows.
_VALID_MPAA_RATINGS = {
    v.upper(): v for v in (
        "G", "PG", "PG-13", "R", "NC-17", "Not Rated",
        "TV-Y", "TV-Y7", "TV-G", "TV-PG", "TV-14", "TV-MA",
    )
}
_MPAA_ALIASES = {"NR": "Not Rated", "UNRATED": "Not Rated", "UR": "Not Rated"}


def _normalize_mpaa_rating(raw: Optional[str]) -> Optional[str]:
    """Map a scraped MPAA/TV rating string onto the DB's allowed set.

    Returns None for anything unrecognized (e.g. a parsing artifact) rather
    than letting it trip the check_mpaa_rating constraint.
    """
    if not raw:
        return None
    value = raw.strip().upper()
    if value in _MPAA_ALIASES:
        return _MPAA_ALIASES[value]
    return _VALID_MPAA_RATINGS.get(value)


def ensure_tables():
    """Create tables if they don't exist."""
    import src.models  # noqa: F401
    from src.database.base import Base
    from src.database.session import engine
    Base.metadata.create_all(bind=engine)


def _log_refresh(
    db,
    source: str,
    status: str,
    records_fetched: int = 0,
    records_updated: int = 0,
    records_created: int = 0,
    records_failed: int = 0,
    errors: Optional[list] = None,
    duration_seconds: Optional[int] = None,
):
    """Create a DataRefreshLog entry."""
    log_entry = DataRefreshLog(
        source=source,
        status=status,
        records_fetched=records_fetched,
        records_updated=records_updated,
        records_created=records_created,
        records_failed=records_failed,
        errors=errors,
        duration_seconds=duration_seconds,
        completed_at=datetime.utcnow(),
    )
    db.add(log_entry)
    db.commit()
    return log_entry


def scrape_kim() -> dict:
    """
    Scrape all 26 A-Z index pages from Kids-in-Mind.
    Scores are embedded in the index page text as:
        Title [Year] [MPAA] - Sex.Violence.Language
    No need to visit detail pages. Existing scores are unconditionally
    overwritten (cheap at this volume) so this also catches corrections.
    """
    import httpx
    from bs4 import BeautifulSoup

    ensure_tables()
    db = SessionLocal()
    start_time = datetime.utcnow()

    score_pattern = re.compile(
        r'^(.+?)\s*\[(\d{4})\]\s*\[([^\]]*)\]\s*[-–—]\s*(\d{1,2})\.(\d{1,2})\.(\d{1,2})',
    )

    base_url = "https://kids-in-mind.com"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Reel-Filter/1.0)"
    }

    crawl_delay = 60  # Respect robots.txt Crawl-delay: 30, we use 60 to be safe

    total_fetched = 0
    created = 0
    updated = 0
    failed = 0

    try:
        with httpx.Client(timeout=30, headers=headers, follow_redirects=True) as client:
            for letter in "abcdefghijklmnopqrstuvwxyz":
                url = f"{base_url}/{letter}"
                logger.info(f"Fetching KIM index page: {url}")

                try:
                    resp = client.get(url)
                    resp.raise_for_status()
                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {e}")
                    time.sleep(crawl_delay)
                    continue

                soup = BeautifulSoup(resp.text, "lxml")
                page_text = soup.get_text()

                page_entries = []
                for line in page_text.split("\n"):
                    line = line.strip()
                    m = score_pattern.match(line)
                    if m:
                        title = m.group(1).strip()
                        year = int(m.group(2))
                        mpaa = _normalize_mpaa_rating(m.group(3).strip())
                        sex = int(m.group(4))
                        violence = int(m.group(5))
                        language = int(m.group(6))

                        if all(0 <= s <= 10 for s in [sex, violence, language]):
                            page_entries.append({
                                "title": title,
                                "year": year,
                                "mpaa": mpaa,
                                "sex": sex,
                                "violence": violence,
                                "language": language,
                            })

                # Write this page immediately rather than accumulating
                # everything in memory for ~26 minutes — a crash or network
                # drop partway through then only costs the in-flight page,
                # not the whole crawl, and search results start filling in
                # well before the full run finishes. Each entry still gets
                # its own SAVEPOINT so one bad row (e.g. an unexpected MPAA
                # value tripping a CHECK constraint) can't roll back the
                # rest of the page. Counters are page-local until the page
                # actually commits, since a failed commit rolls all of them
                # back together.
                page_created = 0
                page_updated = 0
                page_failed = 0
                for entry in page_entries:
                    try:
                        with db.begin_nested():
                            existing = db.query(Movie).filter(
                                Movie.title == entry["title"],
                                Movie.year == entry["year"],
                            ).first()

                            if existing:
                                cs = db.query(ContentScore).filter(
                                    ContentScore.movie_id == existing.id
                                ).first()
                                if cs:
                                    cs.sex_nudity = entry["sex"]
                                    cs.violence_gore = entry["violence"]
                                    cs.language_profanity = entry["language"]
                                    cs.scraped_at = datetime.utcnow()
                                    page_updated += 1
                                else:
                                    db.add(ContentScore(
                                        movie_id=existing.id,
                                        sex_nudity=entry["sex"],
                                        violence_gore=entry["violence"],
                                        language_profanity=entry["language"],
                                        source="kids-in-mind",
                                        match_confidence=100.0,
                                    ))
                                    page_created += 1
                            else:
                                # Create a stub movie (will be enriched by OMDb later)
                                placeholder_id = f"kim-{entry['title'][:50]}-{entry['year']}"
                                movie = Movie(
                                    title=entry["title"],
                                    year=entry["year"],
                                    mpaa_rating=entry["mpaa"] if entry["mpaa"] else None,
                                    genre=[],
                                    omdb_id=placeholder_id,
                                    source="kids-in-mind",
                                )
                                db.add(movie)
                                db.flush()

                                db.add(ContentScore(
                                    movie_id=movie.id,
                                    sex_nudity=entry["sex"],
                                    violence_gore=entry["violence"],
                                    language_profanity=entry["language"],
                                    source="kids-in-mind",
                                    match_confidence=100.0,
                                ))
                                page_created += 1
                    except Exception as e:
                        page_failed += 1
                        logger.warning(f"Skipping '{entry['title']}' ({entry['year']}): {e}")

                # The commit itself (as opposed to a single entry) can fail
                # transiently (connection blip, deadlock). Retry a few times
                # before giving up on this page and moving on, rather than
                # aborting the rest of the crawl over what's likely temporary.
                page_committed = False
                max_commit_attempts = 3
                for attempt in range(1, max_commit_attempts + 1):
                    try:
                        db.commit()
                        page_committed = True
                        break
                    except Exception as e:
                        db.rollback()
                        logger.warning(
                            f"  Commit failed for page '{letter}' "
                            f"(attempt {attempt}/{max_commit_attempts}): {e}"
                        )
                        if attempt < max_commit_attempts:
                            time.sleep(5)

                if page_committed:
                    created += page_created
                    updated += page_updated
                    failed += page_failed
                    total_fetched += len(page_entries)
                    logger.info(f"  Wrote {len(page_entries)} entries ({total_fetched} total so far)")
                else:
                    # Rollback undid everything staged for this page, including
                    # the per-entry work that would have counted as created/updated.
                    failed += len(page_entries)
                    logger.error(
                        f"  Giving up on page '{letter}' after {max_commit_attempts} "
                        f"failed commit attempts; continuing to next page"
                    )

                if letter != "z":
                    logger.info(f"  Waiting {crawl_delay}s (crawl delay)...")
                    time.sleep(crawl_delay)

        duration = int((datetime.utcnow() - start_time).total_seconds())
        logger.info(f"KIM scrape complete: {created} created, {updated} updated, {failed} failed")

        status = "success" if failed == 0 else "partial"
        _log_refresh(
            db,
            source="kids-in-mind",
            status=status,
            records_fetched=total_fetched,
            records_created=created,
            records_updated=updated,
            records_failed=failed,
            duration_seconds=duration,
        )

        return {
            "status": status,
            "fetched": total_fetched,
            "created": created,
            "updated": updated,
            "failed": failed,
        }

    except Exception as e:
        db.rollback()
        duration = int((datetime.utcnow() - start_time).total_seconds())
        logger.error(f"KIM scrape failed: {e}")
        _log_refresh(
            db,
            source="kids-in-mind",
            status="failed",
            errors=[{"error": type(e).__name__, "message": str(e)}],
            duration_seconds=duration,
        )
        raise
    finally:
        db.close()


def fetch_omdb(limit: Optional[int] = None) -> dict:
    """
    For each movie that came from KIM (has placeholder omdb_id),
    look it up in OMDb by title+year to get full metadata.

    Automatically stops when the daily quota is hit and reports progress.
    Safe to re-run — skips already-enriched movies.
    """
    from src.integrations.omdb_client import OMDbClient, OMDbRateLimitError

    ensure_tables()
    db = SessionLocal()
    start_time = datetime.utcnow()

    try:
        query = db.query(Movie).filter(Movie.omdb_id.like("kim-%"))
        total_remaining = query.count()

        if total_remaining == 0:
            logger.info("All movies already enriched with OMDb data. Nothing to do.")
            _log_refresh(db, source="omdb", status="success", duration_seconds=0)
            return {"status": "success", "fetched": 0, "matched": 0, "not_found": 0, "remaining": 0}

        movies = query.all()
        if limit:
            movies = movies[:limit]

        logger.info(
            f"Found {total_remaining} movies needing OMDb data. "
            f"Processing {len(movies)} this run."
        )

        fetched = 0
        matched = 0
        not_found = 0
        quota_hit = False
        errors = []

        with OMDbClient() as client:
            for i, movie in enumerate(movies):
                # Captured up front so the exception handlers can always log
                # something useful even if the session ends up needing a
                # rollback before movie's attributes can be lazy-loaded again.
                movie_title, movie_year = movie.title, movie.year
                try:
                    omdb_movie = client.get_by_title(movie.title, movie.year)
                    if omdb_movie is None:
                        omdb_movie = client.get_by_title(movie.title)

                    fetched += 1

                    if omdb_movie:
                        movie.omdb_id = omdb_movie.imdb_id
                        movie.runtime = omdb_movie.runtime
                        movie.genre = omdb_movie.genre
                        movie.mpaa_rating = omdb_movie.mpaa_rating or movie.mpaa_rating
                        movie.plot = omdb_movie.plot
                        movie.director = omdb_movie.director
                        movie.cast = omdb_movie.cast
                        movie.poster_url = omdb_movie.poster_url
                        movie.imdb_rating = omdb_movie.imdb_rating
                        movie.rt_rating = omdb_movie.rt_rating
                        movie.metacritic_rating = omdb_movie.metacritic_rating
                        movie.awards_summary = omdb_movie.awards_summary
                        movie.awards_count = omdb_movie.awards_count
                        movie.nominations_count = omdb_movie.nominations_count
                        movie.source = "omdb"

                        # Committed per-movie rather than every 50: OMDb calls
                        # (rate-limited, quota-metered) already happened by
                        # this point, so a batched commit failing would waste
                        # already-spent quota by forcing a re-fetch on retry.
                        try:
                            db.commit()
                            matched += 1
                        except IntegrityError:
                            # Two KIM placeholder rows resolved to the same
                            # real OMDb ID (a duplicate title/year entry from
                            # the crawl). Skip this one instead of losing
                            # everything else committed so far this run.
                            db.rollback()
                            not_found += 1
                            errors.append({
                                "movie_title": movie_title,
                                "error": "IntegrityError",
                                "message": f"omdb_id {omdb_movie.imdb_id} already used by another movie (likely a duplicate KIM entry)",
                            })
                    else:
                        not_found += 1

                    if (i + 1) % 50 == 0:
                        remaining = total_remaining - fetched
                        logger.info(
                            f"  Progress: {fetched}/{len(movies)} fetched, "
                            f"{matched} matched, {not_found} not found, "
                            f"~{remaining} remaining total"
                        )

                except OMDbRateLimitError:
                    quota_hit = True
                    logger.warning(
                        f"OMDb daily quota reached after {fetched} requests. "
                        f"Will continue automatically on the next scheduled run."
                    )
                    break

                except Exception as e:
                    db.rollback()
                    logger.warning(f"  Error fetching '{movie_title}' ({movie_year}): {e}")
                    not_found += 1
                    errors.append({
                        "movie_title": movie_title,
                        "error": type(e).__name__,
                        "message": str(e),
                    })

        remaining = total_remaining - fetched
        duration = int((datetime.utcnow() - start_time).total_seconds())

        logger.info(
            f"OMDb enrichment summary: fetched={fetched} matched={matched} "
            f"not_found={not_found} remaining={remaining}"
        )

        status = "success" if not errors and not quota_hit else "partial"
        _log_refresh(
            db,
            source="omdb",
            status=status,
            records_fetched=fetched,
            records_updated=matched,
            records_failed=not_found,
            errors=errors if errors else None,
            duration_seconds=duration,
        )

        return {
            "status": status,
            "fetched": fetched,
            "matched": matched,
            "not_found": not_found,
            "remaining": remaining,
            "quota_hit": quota_hit,
        }

    except Exception as e:
        db.rollback()
        duration = int((datetime.utcnow() - start_time).total_seconds())
        logger.error(f"OMDb enrichment failed: {e}")
        _log_refresh(
            db,
            source="omdb",
            status="failed",
            errors=[{"error": type(e).__name__, "message": str(e)}],
            duration_seconds=duration,
        )
        raise
    finally:
        db.close()
