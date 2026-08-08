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

from src.database.session import SessionLocal
from src.models.movie import Movie
from src.models.content_score import ContentScore
from src.models.data_refresh_log import DataRefreshLog

logger = logging.getLogger(__name__)


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

    all_entries = []
    crawl_delay = 60  # Respect robots.txt Crawl-delay: 30, we use 60 to be safe

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

                for line in page_text.split("\n"):
                    line = line.strip()
                    m = score_pattern.match(line)
                    if m:
                        title = m.group(1).strip()
                        year = int(m.group(2))
                        mpaa = m.group(3).strip()
                        sex = int(m.group(4))
                        violence = int(m.group(5))
                        language = int(m.group(6))

                        if all(0 <= s <= 10 for s in [sex, violence, language]):
                            all_entries.append({
                                "title": title,
                                "year": year,
                                "mpaa": mpaa,
                                "sex": sex,
                                "violence": violence,
                                "language": language,
                            })

                logger.info(f"  Found {len(all_entries)} total entries so far")

                if letter != "z":
                    logger.info(f"  Waiting {crawl_delay}s (crawl delay)...")
                    time.sleep(crawl_delay)

        logger.info(f"Scraped {len(all_entries)} movies from Kids-in-Mind")

        # Each entry gets its own SAVEPOINT so one bad row (e.g. an
        # unexpected MPAA value tripping a CHECK constraint) can't roll back
        # the entire batch after a ~26-minute crawl. Commit periodically too,
        # so progress survives even if the process is killed partway through.
        created = 0
        updated = 0
        failed = 0
        for i, entry in enumerate(all_entries):
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
                            updated += 1
                        else:
                            db.add(ContentScore(
                                movie_id=existing.id,
                                sex_nudity=entry["sex"],
                                violence_gore=entry["violence"],
                                language_profanity=entry["language"],
                                source="kids-in-mind",
                                match_confidence=100.0,
                            ))
                            created += 1
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
                        created += 1
            except Exception as e:
                failed += 1
                logger.warning(f"Skipping '{entry['title']}' ({entry['year']}): {e}")

            if (i + 1) % 200 == 0:
                db.commit()
                logger.info(f"  DB write progress: {i + 1}/{len(all_entries)}")

        db.commit()
        duration = int((datetime.utcnow() - start_time).total_seconds())
        logger.info(f"KIM scrape complete: {created} created, {updated} updated, {failed} failed")

        status = "success" if failed == 0 else "partial"
        _log_refresh(
            db,
            source="kids-in-mind",
            status=status,
            records_fetched=len(all_entries),
            records_created=created,
            records_updated=updated,
            records_failed=failed,
            duration_seconds=duration,
        )

        return {
            "status": status,
            "fetched": len(all_entries),
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
                        matched += 1
                    else:
                        not_found += 1

                    if (i + 1) % 50 == 0:
                        db.commit()
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
                    logger.warning(f"  Error fetching '{movie.title}' ({movie.year}): {e}")
                    not_found += 1
                    errors.append({
                        "movie_title": movie.title,
                        "error": type(e).__name__,
                        "message": str(e),
                    })

        db.commit()

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
