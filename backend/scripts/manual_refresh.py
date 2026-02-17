"""Manual data refresh script for development.

Run this script to manually trigger data refresh operations
without waiting for the Celery Beat schedule.

Usage:
    python scripts/manual_refresh.py --omdb          # Refresh OMDb data only
    python scripts/manual_refresh.py --kim            # Refresh KIM data only
    python scripts/manual_refresh.py --all            # Refresh all data
    python scripts/manual_refresh.py --seed           # Seed with sample data
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parents[1]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def refresh_omdb(imdb_ids=None):
    """Manually refresh OMDb movie data."""
    from src.jobs.weekly_refresh import refresh_omdb_data, POPULAR_IMDB_IDS

    ids = imdb_ids or POPULAR_IMDB_IDS
    logger.info(f"Starting OMDb refresh for {len(ids)} movies...")

    # Call the task function directly (not via Celery)
    result = refresh_omdb_data.apply(args=[], kwargs={"imdb_ids": ids}).get()
    logger.info(f"OMDb refresh result: {result}")
    return result


def refresh_kim():
    """Manually refresh Kids-in-Mind content scores."""
    from src.jobs.weekly_refresh import refresh_kim_data

    logger.info("Starting KIM content score refresh...")
    result = refresh_kim_data.apply().get()
    logger.info(f"KIM refresh result: {result}")
    return result


def seed_sample_data():
    """Seed database with sample movie data (no API calls needed)."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.database.base import Base
    from src.models.movie import Movie
    from src.models.content_score import ContentScore

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://reel_filter_user:dev_password_change_in_production@localhost:5432/reel_filter",
    )

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if data already exists
        count = db.query(Movie).count()
        if count > 0:
            logger.info(f"Database already has {count} movies. Skipping seed.")
            return

        logger.info("Seeding sample movie data...")

        sample_movies = [
            {
                "title": "The Matrix",
                "year": 1999,
                "runtime": 136,
                "genre": ["Action", "Sci-Fi"],
                "mpaa_rating": "R",
                "plot": "A computer hacker learns from mysterious rebels about the true nature of his reality.",
                "director": "Lana Wachowski, Lilly Wachowski",
                "cast": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"],
                "poster_url": "https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg",
                "imdb_rating": 8.7,
                "rt_rating": 87,
                "metacritic_rating": 73,
                "awards_summary": "Won 4 Oscars. 42 wins & 51 nominations total",
                "awards_count": 42,
                "nominations_count": 51,
                "omdb_id": "tt0133093",
                "content": {"sex": 3, "violence": 8, "language": 5},
            },
            {
                "title": "Finding Nemo",
                "year": 2003,
                "runtime": 100,
                "genre": ["Animation", "Adventure", "Comedy", "Family"],
                "mpaa_rating": "G",
                "plot": "A clownfish sets out on a journey to bring his captured son home.",
                "director": "Andrew Stanton, Lee Unkrich",
                "cast": ["Albert Brooks", "Ellen DeGeneres", "Alexander Gould"],
                "poster_url": "https://m.media-amazon.com/images/M/MV5BZjMxYzBhZjctMjMxZC00YzlhLWIyNDUtNDQ1Y2Q5NjJkOGM3XkEyXkFqcGdeQXVyNjY1MDY4MTA@._V1_SX300.jpg",
                "imdb_rating": 8.1,
                "rt_rating": 99,
                "metacritic_rating": 90,
                "awards_summary": "Won 1 Oscar. 47 wins & 63 nominations total",
                "awards_count": 47,
                "nominations_count": 63,
                "omdb_id": "tt0266543",
                "content": {"sex": 0, "violence": 2, "language": 0},
            },
            {
                "title": "The Dark Knight",
                "year": 2008,
                "runtime": 152,
                "genre": ["Action", "Crime", "Drama"],
                "mpaa_rating": "PG-13",
                "plot": "Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                "director": "Christopher Nolan",
                "cast": ["Christian Bale", "Heath Ledger", "Aaron Eckhart"],
                "poster_url": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg",
                "imdb_rating": 9.0,
                "rt_rating": 94,
                "metacritic_rating": 84,
                "awards_summary": "Won 2 Oscars. 159 wins & 163 nominations total",
                "awards_count": 159,
                "nominations_count": 163,
                "omdb_id": "tt0468569",
                "content": {"sex": 2, "violence": 7, "language": 4},
            },
            {
                "title": "The Godfather",
                "year": 1972,
                "runtime": 175,
                "genre": ["Crime", "Drama"],
                "mpaa_rating": "R",
                "plot": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
                "director": "Francis Ford Coppola",
                "cast": ["Marlon Brando", "Al Pacino", "James Caan"],
                "imdb_rating": 9.2,
                "rt_rating": 97,
                "metacritic_rating": 100,
                "awards_summary": "Won 3 Oscars. 32 wins & 30 nominations total",
                "awards_count": 32,
                "nominations_count": 30,
                "omdb_id": "tt0068646",
                "content": {"sex": 3, "violence": 8, "language": 6},
            },
            {
                "title": "Toy Story",
                "year": 1995,
                "runtime": 81,
                "genre": ["Animation", "Adventure", "Comedy", "Family"],
                "mpaa_rating": "G",
                "plot": "A cowboy doll is profoundly threatened when a new spaceman figure supplants him as top toy.",
                "director": "John Lasseter",
                "cast": ["Tom Hanks", "Tim Allen", "Don Rickles"],
                "imdb_rating": 8.3,
                "rt_rating": 100,
                "metacritic_rating": 95,
                "awards_summary": "Nominated for 3 Oscars. 30 wins & 23 nominations total",
                "awards_count": 30,
                "nominations_count": 23,
                "omdb_id": "tt0114709",
                "content": {"sex": 0, "violence": 1, "language": 1},
            },
            {
                "title": "Inception",
                "year": 2010,
                "runtime": 148,
                "genre": ["Action", "Adventure", "Sci-Fi"],
                "mpaa_rating": "PG-13",
                "plot": "A thief who steals corporate secrets through dream-sharing technology is given the task of planting an idea into the mind of a C.E.O.",
                "director": "Christopher Nolan",
                "cast": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"],
                "poster_url": "https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_SX300.jpg",
                "imdb_rating": 8.8,
                "rt_rating": 87,
                "metacritic_rating": 74,
                "awards_summary": "Won 4 Oscars. 157 wins & 220 nominations total",
                "awards_count": 157,
                "nominations_count": 220,
                "omdb_id": "tt1375666",
                "content": {"sex": 2, "violence": 6, "language": 4},
            },
            {
                "title": "Pulp Fiction",
                "year": 1994,
                "runtime": 154,
                "genre": ["Crime", "Drama"],
                "mpaa_rating": "R",
                "plot": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
                "director": "Quentin Tarantino",
                "cast": ["John Travolta", "Uma Thurman", "Samuel L. Jackson"],
                "poster_url": "https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItYzViMjE3YzI5MjljXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg",
                "imdb_rating": 8.9,
                "rt_rating": 92,
                "metacritic_rating": 94,
                "awards_summary": "Won 1 Oscar. 69 wins & 75 nominations total",
                "awards_count": 69,
                "nominations_count": 75,
                "omdb_id": "tt0110912",
                "content": {"sex": 5, "violence": 9, "language": 10},
            },
            {
                "title": "Schindler's List",
                "year": 1993,
                "runtime": 195,
                "genre": ["Biography", "Drama", "History"],
                "mpaa_rating": "R",
                "plot": "In German-occupied Poland during World War II, industrialist Oskar Schindler gradually becomes concerned for his Jewish workforce.",
                "director": "Steven Spielberg",
                "cast": ["Liam Neeson", "Ralph Fiennes", "Ben Kingsley"],
                "imdb_rating": 9.0,
                "rt_rating": 98,
                "metacritic_rating": 94,
                "awards_summary": "Won 7 Oscars. 91 wins & 49 nominations total",
                "awards_count": 91,
                "nominations_count": 49,
                "omdb_id": "tt0108052",
                "content": {"sex": 4, "violence": 9, "language": 5},
            },
            {
                "title": "Frozen",
                "year": 2013,
                "runtime": 102,
                "genre": ["Animation", "Adventure", "Comedy", "Family", "Fantasy", "Musical"],
                "mpaa_rating": "PG",
                "plot": "When the newly crowned Queen Elsa accidentally uses her power to turn things into ice to curse her home in infinite winter, her sister Anna teams up with a mountain man and his reindeer to change the weather condition.",
                "director": "Chris Buck, Jennifer Lee",
                "cast": ["Kristen Bell", "Idina Menzel", "Jonathan Groff"],
                "poster_url": "https://m.media-amazon.com/images/M/MV5BMTQ1MjQwMTE5OF5BMl5BanBnXkFtZTgwNjk3MTcyMDE@._V1_SX300.jpg",
                "imdb_rating": 7.4,
                "rt_rating": 90,
                "metacritic_rating": 74,
                "awards_summary": "Won 2 Oscars. 82 wins & 60 nominations total",
                "awards_count": 82,
                "nominations_count": 60,
                "omdb_id": "tt2294629",
                "content": {"sex": 1, "violence": 3, "language": 1},
            },
            {
                "title": "The Silence of the Lambs",
                "year": 1991,
                "runtime": 118,
                "genre": ["Crime", "Drama", "Thriller"],
                "mpaa_rating": "R",
                "plot": "A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer.",
                "director": "Jonathan Demme",
                "cast": ["Jodie Foster", "Anthony Hopkins", "Lawrence A. Bonney"],
                "imdb_rating": 8.6,
                "rt_rating": 95,
                "metacritic_rating": 85,
                "awards_summary": "Won 5 Oscars. 65 wins & 36 nominations total",
                "awards_count": 65,
                "nominations_count": 36,
                "omdb_id": "tt0102926",
                "content": {"sex": 5, "violence": 8, "language": 6},
            },
        ]

        for movie_data in sample_movies:
            content = movie_data.pop("content")
            movie = Movie(**movie_data)
            db.add(movie)
            db.flush()

            content_score = ContentScore(
                movie_id=movie.id,
                sex_nudity=content["sex"],
                violence_gore=content["violence"],
                language_profanity=content["language"],
                source="kids-in-mind",
                match_confidence=95.0,
                manually_reviewed=False,
            )
            db.add(content_score)
            logger.info(f"  Added: {movie.title} ({movie.year})")

        db.commit()
        logger.info(f"Successfully seeded {len(sample_movies)} movies!")

    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Manual data refresh for Reel-Filter")
    parser.add_argument("--omdb", action="store_true", help="Refresh OMDb data")
    parser.add_argument("--kim", action="store_true", help="Refresh KIM data")
    parser.add_argument("--all", action="store_true", help="Refresh all data sources")
    parser.add_argument("--seed", action="store_true", help="Seed sample data")
    args = parser.parse_args()

    if not any([args.omdb, args.kim, args.all, args.seed]):
        parser.print_help()
        return

    if args.seed:
        seed_sample_data()

    if args.omdb or args.all:
        refresh_omdb()

    if args.kim or args.all:
        refresh_kim()


if __name__ == "__main__":
    main()
