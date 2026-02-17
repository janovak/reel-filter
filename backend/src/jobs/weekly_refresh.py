"""Weekly data refresh tasks.

Celery tasks for:
1. Fetching movie metadata from OMDb API
2. Scraping content scores from Kids-in-Mind
3. Fuzzy matching between the two datasets
4. Logging refresh results to DataRefreshLog

Implements idempotent upsert operations using omdb_id as unique key.
"""
import logging
from datetime import datetime
from typing import Optional

from src.jobs.celery_app import celery_app
from src.database.session import SessionLocal
from src.models.movie import Movie
from src.models.content_score import ContentScore
from src.models.data_refresh_log import DataRefreshLog
from src.integrations.omdb_client import OMDbClient, OMDbMovie, OMDbClientError
from src.integrations.kim_scraper import KIMScraper, KIMContentScore, KIMScraperError
from src.services.matching_service import MatchingService

logger = logging.getLogger(__name__)

# Sample popular movies to fetch from OMDb (can be expanded)
POPULAR_IMDB_IDS = [
    "tt0111161",  # The Shawshank Redemption
    "tt0068646",  # The Godfather
    "tt0071562",  # The Godfather Part II
    "tt0468569",  # The Dark Knight
    "tt0050083",  # 12 Angry Men
    "tt0108052",  # Schindler's List
    "tt0167260",  # LOTR: Return of the King
    "tt0110912",  # Pulp Fiction
    "tt0060196",  # The Good, the Bad and the Ugly
    "tt0120737",  # LOTR: Fellowship of the Ring
    "tt0137523",  # Fight Club
    "tt0109830",  # Forrest Gump
    "tt1375666",  # Inception
    "tt0133093",  # The Matrix
    "tt0073486",  # One Flew Over the Cuckoo's Nest
    "tt0099685",  # Goodfellas
    "tt0076759",  # Star Wars: A New Hope
    "tt0114369",  # Se7en
    "tt0102926",  # Silence of the Lambs
    "tt0038650",  # It's a Wonderful Life
    "tt0114709",  # Toy Story
    "tt0266543",  # Finding Nemo
    "tt0435761",  # Toy Story 3
    "tt2380307",  # Coco
    "tt0910970",  # WALL-E
    "tt0198781",  # Monsters, Inc.
    "tt0126029",  # Shrek
    "tt0317705",  # The Incredibles
    "tt2096673",  # Inside Out
    "tt0382932",  # Ratatouille
]


def _upsert_movie(db, omdb_movie: OMDbMovie) -> Movie:
    """Upsert a movie record using omdb_id as unique identifier."""
    existing = db.query(Movie).filter(Movie.omdb_id == omdb_movie.imdb_id).first()

    if existing:
        # Update existing record
        existing.title = omdb_movie.title
        existing.year = omdb_movie.year
        existing.runtime = omdb_movie.runtime
        existing.genre = omdb_movie.genre
        existing.mpaa_rating = omdb_movie.mpaa_rating
        existing.plot = omdb_movie.plot
        existing.director = omdb_movie.director
        existing.cast = omdb_movie.cast
        existing.poster_url = omdb_movie.poster_url
        existing.imdb_rating = omdb_movie.imdb_rating
        existing.rt_rating = omdb_movie.rt_rating
        existing.metacritic_rating = omdb_movie.metacritic_rating
        existing.awards_summary = omdb_movie.awards_summary
        existing.awards_count = omdb_movie.awards_count
        existing.nominations_count = omdb_movie.nominations_count
        return existing
    else:
        # Create new record
        movie = Movie(
            title=omdb_movie.title,
            year=omdb_movie.year,
            runtime=omdb_movie.runtime,
            genre=omdb_movie.genre,
            mpaa_rating=omdb_movie.mpaa_rating,
            plot=omdb_movie.plot,
            director=omdb_movie.director,
            cast=omdb_movie.cast,
            poster_url=omdb_movie.poster_url,
            imdb_rating=omdb_movie.imdb_rating,
            rt_rating=omdb_movie.rt_rating,
            metacritic_rating=omdb_movie.metacritic_rating,
            awards_summary=omdb_movie.awards_summary,
            awards_count=omdb_movie.awards_count,
            nominations_count=omdb_movie.nominations_count,
            omdb_id=omdb_movie.imdb_id,
            source="omdb",
        )
        db.add(movie)
        db.flush()
        return movie


def _upsert_content_score(
    db, movie: Movie, kim_score: KIMContentScore, confidence: float
) -> ContentScore:
    """Upsert content score for a movie."""
    existing = db.query(ContentScore).filter(ContentScore.movie_id == movie.id).first()

    if existing:
        existing.sex_nudity = kim_score.sex_nudity
        existing.violence_gore = kim_score.violence_gore
        existing.language_profanity = kim_score.language_profanity
        existing.match_confidence = confidence
        existing.scraped_at = datetime.utcnow()
        return existing
    else:
        cs = ContentScore(
            movie_id=movie.id,
            sex_nudity=kim_score.sex_nudity,
            violence_gore=kim_score.violence_gore,
            language_profanity=kim_score.language_profanity,
            source="kids-in-mind",
            match_confidence=confidence,
            manually_reviewed=False,
        )
        db.add(cs)
        return cs


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


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="src.jobs.weekly_refresh.refresh_omdb_data",
)
def refresh_omdb_data(self, imdb_ids: Optional[list] = None):
    """
    Fetch/update movie metadata from OMDb API.

    Args:
        imdb_ids: Optional list of IMDb IDs to refresh. Defaults to POPULAR_IMDB_IDS.
    """
    start_time = datetime.utcnow()
    ids_to_fetch = imdb_ids or POPULAR_IMDB_IDS

    db = SessionLocal()
    records_fetched = 0
    records_updated = 0
    records_created = 0
    records_failed = 0
    errors = []

    try:
        with OMDbClient() as client:
            for imdb_id in ids_to_fetch:
                try:
                    omdb_movie = client.get_by_imdb_id(imdb_id)
                    if omdb_movie is None:
                        records_failed += 1
                        errors.append({
                            "imdb_id": imdb_id,
                            "error": "NotFound",
                            "message": f"Movie {imdb_id} not found in OMDb",
                        })
                        continue

                    records_fetched += 1

                    # Check if movie already exists
                    existing = db.query(Movie).filter(Movie.omdb_id == imdb_id).first()
                    _upsert_movie(db, omdb_movie)

                    if existing:
                        records_updated += 1
                    else:
                        records_created += 1

                except OMDbClientError as e:
                    records_failed += 1
                    errors.append({
                        "imdb_id": imdb_id,
                        "error": type(e).__name__,
                        "message": str(e),
                    })
                    logger.warning(f"Failed to fetch {imdb_id}: {e}")

        db.commit()

        duration = int((datetime.utcnow() - start_time).total_seconds())
        status = "success" if records_failed == 0 else "partial"

        _log_refresh(
            db,
            source="omdb",
            status=status,
            records_fetched=records_fetched,
            records_updated=records_updated,
            records_created=records_created,
            records_failed=records_failed,
            errors=errors if errors else None,
            duration_seconds=duration,
        )

        logger.info(
            f"OMDb refresh complete: {records_fetched} fetched, "
            f"{records_created} created, {records_updated} updated, "
            f"{records_failed} failed ({duration}s)"
        )

        return {
            "status": status,
            "records_fetched": records_fetched,
            "records_created": records_created,
            "records_updated": records_updated,
            "records_failed": records_failed,
        }

    except Exception as exc:
        db.rollback()
        duration = int((datetime.utcnow() - start_time).total_seconds())

        _log_refresh(
            db,
            source="omdb",
            status="failed",
            records_fetched=records_fetched,
            records_failed=records_failed,
            errors=[{"error": type(exc).__name__, "message": str(exc)}],
            duration_seconds=duration,
        )

        logger.error(f"OMDb refresh failed: {exc}")

        # Retry with exponential backoff
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="src.jobs.weekly_refresh.refresh_kim_data",
)
def refresh_kim_data(self):
    """
    Scrape content scores from Kids-in-Mind and match to existing movies.
    Uses fuzzy matching to pair KIM content scores with OMDb movie records.
    """
    start_time = datetime.utcnow()
    db = SessionLocal()
    records_fetched = 0
    records_updated = 0
    records_created = 0
    records_failed = 0
    errors = []

    try:
        # Get all movies that need content scores
        movies = db.query(Movie).outerjoin(ContentScore).filter(
            ContentScore.id.is_(None)
        ).all()

        if not movies:
            logger.info("All movies already have content scores. Skipping KIM refresh.")
            _log_refresh(db, source="kids-in-mind", status="success", duration_seconds=0)
            return {"status": "success", "message": "No movies need content scores"}

        matcher = MatchingService()

        with KIMScraper() as scraper:
            # Fetch KIM listings (first few pages)
            kim_entries = []
            for page in range(1, 6):  # Fetch 5 pages
                try:
                    entries = scraper.get_movie_list(page=page)
                    kim_entries.extend(entries)
                except Exception as e:
                    logger.warning(f"Failed to fetch KIM page {page}: {e}")

            logger.info(f"Found {len(kim_entries)} KIM entries")

            # For each unscored movie, try to find and scrape content scores
            for movie in movies:
                try:
                    # Try fuzzy matching
                    result = matcher.match_single(
                        movie.title,
                        movie.year,
                        kim_entries,
                    )

                    if result and result.kim_url:
                        # Scrape the matched page
                        kim_score = scraper.scrape_movie_scores(result.kim_url)
                        if kim_score:
                            records_fetched += 1
                            _upsert_content_score(db, movie, kim_score, result.confidence)
                            if result.auto_matched:
                                records_created += 1
                            else:
                                records_updated += 1  # Needs review but still stored

                except KIMScraperError as e:
                    records_failed += 1
                    errors.append({
                        "movie_title": movie.title,
                        "error": "ScrapingError",
                        "message": str(e),
                    })
                except Exception as e:
                    records_failed += 1
                    errors.append({
                        "movie_title": movie.title,
                        "error": type(e).__name__,
                        "message": str(e),
                    })

        db.commit()

        duration = int((datetime.utcnow() - start_time).total_seconds())
        status = "success" if records_failed == 0 else "partial"

        _log_refresh(
            db,
            source="kids-in-mind",
            status=status,
            records_fetched=records_fetched,
            records_updated=records_updated,
            records_created=records_created,
            records_failed=records_failed,
            errors=errors if errors else None,
            duration_seconds=duration,
        )

        logger.info(
            f"KIM refresh complete: {records_fetched} scraped, "
            f"{records_created} matched, {records_failed} failed ({duration}s)"
        )

        return {
            "status": status,
            "records_fetched": records_fetched,
            "records_created": records_created,
            "records_updated": records_updated,
            "records_failed": records_failed,
        }

    except Exception as exc:
        db.rollback()
        duration = int((datetime.utcnow() - start_time).total_seconds())

        _log_refresh(
            db,
            source="kids-in-mind",
            status="failed",
            errors=[{"error": type(exc).__name__, "message": str(exc)}],
            duration_seconds=duration,
        )

        logger.error(f"KIM refresh failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        db.close()
