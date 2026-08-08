"""Manual data refresh script.

Handles the full data pipeline:
1. Scrape Kids-in-Mind A-Z index pages → content scores (no API key needed)
2. Look up each KIM movie in OMDb → full metadata (needs API key, quota-aware)

Usage:
    python scripts/manual_refresh.py --kim            # Step 1: scrape KIM scores
    python scripts/manual_refresh.py --omdb           # Step 2: fetch OMDb for unmatched KIM movies
    python scripts/manual_refresh.py --all            # Both steps in order
    python scripts/manual_refresh.py --seed           # Seed sample data (no network needed)
    python scripts/manual_refresh.py --omdb --limit 500  # Fetch at most 500 from OMDb
"""
import os
import sys
import re
import time
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

sys.path.insert(0, str(Path(__file__).parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def get_db():
    from src.database.session import SessionLocal
    return SessionLocal()


def ensure_tables():
    """Create tables if they don't exist."""
    import src.models  # noqa: F401
    from src.database.base import Base
    from src.database.session import engine
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Step 1: Scrape Kids-in-Mind A-Z index pages
# ---------------------------------------------------------------------------

def scrape_kim():
    """
    Scrape all 26 A-Z index pages from Kids-in-Mind.
    Scores are embedded in the index page text as:
        Title [Year] [MPAA] - Sex.Violence.Language
    No need to visit detail pages.
    """
    import httpx
    from bs4 import BeautifulSoup
    from src.models.content_score import ContentScore
    from src.models.movie import Movie

    ensure_tables()
    db = get_db()

    # Regex to parse: "Title [2003] [PG-13] – 4.5.3" or similar
    # The scores appear as "X.Y.Z" where X=sex, Y=violence, Z=language
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

                # Parse each line for score patterns
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

                        # Validate scores are 0-10
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

                # Rate limit between pages
                if letter != "z":
                    logger.info(f"  Waiting {crawl_delay}s (crawl delay)...")
                    time.sleep(crawl_delay)

        logger.info(f"\nScraped {len(all_entries)} movies from Kids-in-Mind")

        # Store in database — create Movie stubs + ContentScore records
        created = 0
        skipped = 0
        for entry in all_entries:
            # Check if we already have this movie (by title+year)
            existing = db.query(Movie).filter(
                Movie.title == entry["title"],
                Movie.year == entry["year"],
            ).first()

            if existing:
                # Update or create content score
                cs = db.query(ContentScore).filter(
                    ContentScore.movie_id == existing.id
                ).first()
                if cs:
                    cs.sex_nudity = entry["sex"]
                    cs.violence_gore = entry["violence"]
                    cs.language_profanity = entry["language"]
                    cs.scraped_at = datetime.utcnow()
                    skipped += 1
                else:
                    cs = ContentScore(
                        movie_id=existing.id,
                        sex_nudity=entry["sex"],
                        violence_gore=entry["violence"],
                        language_profanity=entry["language"],
                        source="kids-in-mind",
                        match_confidence=100.0,
                    )
                    db.add(cs)
                    created += 1
            else:
                # Create a stub movie (will be enriched by OMDb later)
                # Use a placeholder omdb_id that we'll replace
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

                cs = ContentScore(
                    movie_id=movie.id,
                    sex_nudity=entry["sex"],
                    violence_gore=entry["violence"],
                    language_profanity=entry["language"],
                    source="kids-in-mind",
                    match_confidence=100.0,
                )
                db.add(cs)
                created += 1

        db.commit()
        logger.info(f"KIM scrape complete: {created} created, {skipped} updated")

    except Exception as e:
        db.rollback()
        logger.error(f"KIM scrape failed: {e}")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Step 2: Enrich KIM movies with OMDb metadata
# ---------------------------------------------------------------------------

def fetch_omdb(limit: Optional[int] = None):
    """
    For each movie that came from KIM (has placeholder omdb_id),
    look it up in OMDb by title+year to get full metadata.

    Automatically stops when the daily quota is hit and reports progress.
    Safe to re-run — skips already-enriched movies.
    """
    from src.integrations.omdb_client import OMDbClient, OMDbRateLimitError
    from src.models.movie import Movie

    ensure_tables()
    db = get_db()

    try:
        # Find movies that still have KIM placeholder IDs (not yet enriched)
        query = db.query(Movie).filter(Movie.omdb_id.like("kim-%"))
        total_remaining = query.count()

        if total_remaining == 0:
            logger.info("All movies already enriched with OMDb data. Nothing to do.")
            return

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

        with OMDbClient() as client:
            for i, movie in enumerate(movies):
                try:
                    # Look up by title + year
                    omdb_movie = client.get_by_title(movie.title, movie.year)

                    if omdb_movie is None:
                        # Try without year (year might differ by 1)
                        omdb_movie = client.get_by_title(movie.title)

                    fetched += 1

                    if omdb_movie:
                        # Enrich the movie record
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

                    # Progress logging every 50 movies
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
                        f"\nOMDb daily quota reached after {fetched} requests. "
                        f"Run this command again tomorrow to continue."
                    )
                    break

                except Exception as e:
                    logger.warning(f"  Error fetching '{movie.title}' ({movie.year}): {e}")
                    not_found += 1

        db.commit()

        remaining = total_remaining - fetched
        logger.info(f"\nOMDb enrichment summary:")
        logger.info(f"  Fetched:    {fetched}")
        logger.info(f"  Matched:    {matched}")
        logger.info(f"  Not found:  {not_found}")
        logger.info(f"  Remaining:  {remaining}")

        if quota_hit:
            logger.info(f"\n  Quota hit. Re-run tomorrow to process the remaining {remaining} movies.")
        elif remaining > 0:
            logger.info(f"\n  Run again with --omdb to process more.")
        else:
            logger.info(f"\n  All movies enriched!")

    except Exception as e:
        db.rollback()
        logger.error(f"OMDb enrichment failed: {e}")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Seed sample data (no network needed)
# ---------------------------------------------------------------------------

def seed_sample_data():
    """Seed database with sample movie data for testing."""
    from src.models.movie import Movie
    from src.models.content_score import ContentScore

    ensure_tables()
    db = get_db()

    try:
        if db.query(Movie).count() > 0:
            logger.info("Database already has data. Skipping seed.")
            return

        logger.info("Seeding sample movie data...")

        samples = [
            ("The Matrix", 1999, "R", ["Action", "Sci-Fi"], "tt0133093", 8.7, 87, 73, 3, 8, 5,
             "A computer hacker learns the true nature of his reality.",
             "Lana Wachowski, Lilly Wachowski", ["Keanu Reeves", "Laurence Fishburne"],
             "Won 4 Oscars. 42 wins & 51 nominations total", 42, 51),
            ("Finding Nemo", 2003, "G", ["Animation", "Adventure", "Comedy"], "tt0266543", 8.1, 99, 90, 0, 2, 0,
             "A clownfish sets out to bring his captured son home.",
             "Andrew Stanton", ["Albert Brooks", "Ellen DeGeneres"],
             "Won 1 Oscar. 47 wins & 63 nominations total", 47, 63),
            ("The Dark Knight", 2008, "PG-13", ["Action", "Crime", "Drama"], "tt0468569", 9.0, 94, 84, 2, 7, 4,
             "Batman faces the Joker's havoc on Gotham.",
             "Christopher Nolan", ["Christian Bale", "Heath Ledger"],
             "Won 2 Oscars. 159 wins & 163 nominations total", 159, 163),
            ("The Godfather", 1972, "R", ["Crime", "Drama"], "tt0068646", 9.2, 97, 100, 3, 8, 6,
             "An organized crime dynasty's patriarch transfers control to his son.",
             "Francis Ford Coppola", ["Marlon Brando", "Al Pacino"],
             "Won 3 Oscars. 32 wins & 30 nominations total", 32, 30),
            ("Toy Story", 1995, "G", ["Animation", "Adventure", "Comedy"], "tt0114709", 8.3, 100, 95, 0, 1, 1,
             "A cowboy doll is threatened when a new spaceman supplants him.",
             "John Lasseter", ["Tom Hanks", "Tim Allen"],
             "Nominated for 3 Oscars. 30 wins & 23 nominations total", 30, 23),
            ("Pulp Fiction", 1994, "R", ["Crime", "Drama"], "tt0110912", 8.9, 92, 94, 6, 9, 10,
             "Intertwining tales of violence and redemption.",
             "Quentin Tarantino", ["John Travolta", "Uma Thurman", "Samuel L. Jackson"],
             "Won 1 Oscar. 69 wins & 75 nominations total", 69, 75),
            ("Inception", 2010, "PG-13", ["Action", "Adventure", "Sci-Fi"], "tt1375666", 8.8, 87, 74, 2, 6, 3,
             "A thief plants an idea in a CEO's mind through dream-sharing technology.",
             "Christopher Nolan", ["Leonardo DiCaprio", "Joseph Gordon-Levitt"],
             "Won 4 Oscars. 157 wins & 220 nominations total", 157, 220),
            ("Frozen", 2013, "PG", ["Animation", "Adventure", "Comedy", "Family"], "tt2294629", 7.4, 90, 74, 1, 3, 1,
             "A fearless princess sets off to find her estranged sister.",
             "Chris Buck, Jennifer Lee", ["Kristen Bell", "Idina Menzel"],
             "Won 2 Oscars. 82 wins & 60 nominations total", 82, 60),
            ("Deadpool", 2016, "R", ["Action", "Comedy"], "tt1431045", 8.0, 85, 65, 7, 8, 10,
             "A wisecracking mercenary tracks down the man who ruined his looks.",
             "Tim Miller", ["Ryan Reynolds", "Morena Baccarin"],
             "29 wins & 78 nominations total", 29, 78),
            ("The Shawshank Redemption", 1994, "R", ["Drama"], "tt0111161", 9.3, 91, 82, 4, 6, 7,
             "Two convicts form a friendship seeking redemption.",
             "Frank Darabont", ["Tim Robbins", "Morgan Freeman"],
             "Nominated for 7 Oscars. 21 wins & 43 nominations total", 21, 43),
        ]

        for (title, year, mpaa, genres, omdb_id, imdb, rt, mc, sex, vio, lang,
             plot, director, cast, awards, wins, noms) in samples:
            movie = Movie(
                title=title, year=year, mpaa_rating=mpaa, genre=genres,
                omdb_id=omdb_id, imdb_rating=imdb, rt_rating=rt,
                metacritic_rating=mc, plot=plot, director=director, cast=cast,
                awards_summary=awards, awards_count=wins, nominations_count=noms,
            )
            db.add(movie)
            db.flush()

            cs = ContentScore(
                movie_id=movie.id, sex_nudity=sex, violence_gore=vio,
                language_profanity=lang, source="kids-in-mind",
                match_confidence=95.0,
            )
            db.add(cs)
            logger.info(f"  {title} ({year}) S:{sex} V:{vio} L:{lang}")

        db.commit()
        logger.info(f"Seeded {len(samples)} movies.")

    except Exception as e:
        db.rollback()
        logger.error(f"Seed failed: {e}")
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Reel Filter data pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manual_refresh.py --seed              # Quick test with sample data
  python scripts/manual_refresh.py --kim               # Scrape ~5,000 KIM scores (~26 min)
  python scripts/manual_refresh.py --omdb              # Enrich KIM movies via OMDb (quota-aware)
  python scripts/manual_refresh.py --omdb --limit 900  # Fetch at most 900 (stay under free quota)
  python scripts/manual_refresh.py --all               # KIM scrape then OMDb enrichment
""",
    )
    parser.add_argument("--kim", action="store_true", help="Scrape Kids-in-Mind A-Z index pages")
    parser.add_argument("--omdb", action="store_true", help="Enrich KIM movies with OMDb metadata")
    parser.add_argument("--all", action="store_true", help="Run KIM scrape then OMDb enrichment")
    parser.add_argument("--seed", action="store_true", help="Seed sample data (no network needed)")
    parser.add_argument("--limit", type=int, default=None, help="Max movies to fetch from OMDb per run")
    args = parser.parse_args()

    if not any([args.kim, args.omdb, args.all, args.seed]):
        parser.print_help()
        return

    if args.seed:
        seed_sample_data()

    if args.kim or args.all:
        scrape_kim()

    if args.omdb or args.all:
        fetch_omdb(limit=args.limit)


if __name__ == "__main__":
    main()

