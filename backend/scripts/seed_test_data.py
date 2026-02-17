"""Seed test data for development"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from uuid import uuid4

from src.database.base import Base
from src.models.movie import Movie
from src.models.content_score import ContentScore

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://reel_filter_user:dev_password_change_in_production@localhost:5432/reel_filter"
)

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def seed_test_movies():
    """Seed database with test movies"""
    db = SessionLocal()
    
    try:
        print("🌱 Seeding test data...")
        
        # Sample movies with content scores
        test_movies = [
            {
                "title": "The Matrix",
                "year": 1999,
                "runtime": 136,
                "genre": ["Action", "Sci-Fi"],
                "mpaa_rating": "R",
                "plot": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
                "director": "Lana Wachowski, Lilly Wachowski",
                "cast": ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss", "Hugo Weaving"],
                "poster_url": "https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg",
                "imdb_rating": 8.7,
                "rt_rating": 87,
                "metacritic_rating": 73,
                "awards_summary": "Won 4 Oscars. 42 wins & 51 nominations total",
                "awards_count": 42,
                "nominations_count": 51,
                "omdb_id": "tt0133093",
                "content_score": {"sex_nudity": 3, "violence_gore": 8, "language_profanity": 5}
            },
            {
                "title": "Finding Nemo",
                "year": 2003,
                "runtime": 100,
                "genre": ["Animation", "Adventure", "Comedy", "Family"],
                "mpaa_rating": "G",
                "plot": "After his son is captured in the Great Barrier Reef and taken to Sydney, a timid clownfish sets out on a journey to bring him home.",
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
                "content_score": {"sex_nudity": 0, "violence_gore": 2, "language_profanity": 0}
            },
            {
                "title": "The Dark Knight",
                "year": 2008,
                "runtime": 152,
                "genre": ["Action", "Crime", "Drama"],
                "mpaa_rating": "PG-13",
                "plot": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
                "director": "Christopher Nolan",
                "cast": ["Christian Bale", "Heath Ledger", "Aaron Eckhart", "Michael Caine"],
                "poster_url": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg",
                "imdb_rating": 9.0,
                "rt_rating": 94,
                "metacritic_rating": 84,
                "awards_summary": "Won 2 Oscars. 159 wins & 163 nominations total",
                "awards_count": 159,
                "nominations_count": 163,
                "omdb_id": "tt0468569",
                "content_score": {"sex_nudity": 2, "violence_gore": 7, "language_profanity": 4}
            },
            {
                "title": "The Godfather",
                "year": 1972,
                "runtime": 175,
                "genre": ["Crime", "Drama"],
                "mpaa_rating": "R",
                "plot": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
                "director": "Francis Ford Coppola",
                "cast": ["Marlon Brando", "Al Pacino", "James Caan", "Diane Keaton"],
                "imdb_rating": 9.2,
                "rt_rating": 97,
                "metacritic_rating": 100,
                "awards_summary": "Won 3 Oscars. 32 wins & 30 nominations total",
                "awards_count": 32,
                "nominations_count": 30,
                "omdb_id": "tt0068646",
                "content_score": {"sex_nudity": 3, "violence_gore": 8, "language_profanity": 6}
            },
            {
                "title": "Toy Story",
                "year": 1995,
                "runtime": 81,
                "genre": ["Animation", "Adventure", "Comedy", "Family"],
                "mpaa_rating": "G",
                "plot": "A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy's room.",
                "director": "John Lasseter",
                "cast": ["Tom Hanks", "Tim Allen", "Don Rickles", "Jim Varney"],
                "imdb_rating": 8.3,
                "rt_rating": 100,
                "metacritic_rating": 95,
                "awards_summary": "Nominated for 3 Oscars. 30 wins & 23 nominations total",
                "awards_count": 30,
                "nominations_count": 23,
                "omdb_id": "tt0114709",
                "content_score": {"sex_nudity": 0, "violence_gore": 1, "language_profanity": 1}
            }
        ]
        
        # Insert movies
        for movie_data in test_movies:
            # Extract content score data
            content_score_data = movie_data.pop("content_score")
            
            # Create movie
            movie = Movie(**movie_data)
            db.add(movie)
            db.flush()  # Flush to get movie.id
            
            # Create content score
            content_score = ContentScore(
                movie_id=movie.id,
                sex_nudity=content_score_data["sex_nudity"],
                violence_gore=content_score_data["violence_gore"],
                language_profanity=content_score_data["language_profanity"],
                source="kids-in-mind",
                match_confidence=95.0,
                manually_reviewed=False
            )
            db.add(content_score)
            
            print(f"  ✓ Added: {movie.title} ({movie.year})")
        
        # Commit all changes
        db.commit()
        print(f"\n✅ Successfully seeded {len(test_movies)} test movies!")
        
    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Reel-Filter Database Seeder")
    print("="*60 + "\n")
    
    # Check if tables exist
    try:
        engine.connect()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nMake sure to:")
        print("  1. Start database: docker-compose up -d db")
        print("  2. Run migrations: alembic upgrade head")
        sys.exit(1)
    
    # Seed data
    seed_test_movies()
    
    print("\n" + "="*60)
    print("  Next Steps:")
    print("="*60)
    print("  1. Start backend: python src/main.py")
    print("  2. Start frontend: cd ../frontend && npm run dev")
    print("  3. Visit: http://localhost:3000")
    print("  4. Test content filtering with different thresholds!")
    print("")
