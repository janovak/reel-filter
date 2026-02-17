"""MovieService - retrieving single movie details"""
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from src.models.movie import Movie


class MovieService:
    """Service for retrieving movie details"""

    def __init__(self, db: Session):
        self.db = db

    def get_movie_by_id(self, movie_id: str) -> Optional[Movie]:
        """
        Get a single movie by ID with content score eagerly loaded.

        Args:
            movie_id: UUID of the movie

        Returns:
            Movie object with content_score relationship loaded, or None if not found
        """
        return (
            self.db.query(Movie)
            .options(joinedload(Movie.content_score))
            .filter(Movie.id == movie_id)
            .first()
        )
