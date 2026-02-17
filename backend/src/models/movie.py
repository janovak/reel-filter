"""Movie model - comprehensive movie metadata from OMDb API"""
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (
    ARRAY, CheckConstraint, Column, DateTime, Integer, 
    Numeric, String, Text, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from src.database.base import Base


class Movie(Base):
    """Movie entity with metadata from OMDb API"""
    
    __tablename__ = "movies"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Basic information
    title = Column(String(255), nullable=False)
    year = Column(
        Integer, 
        nullable=False,
        # Year validation: 1888 (first film) to 2100 (future planning)
    )
    runtime = Column(Integer, nullable=True)  # Runtime in minutes
    genre = Column(ARRAY(String), nullable=False, default=list)  # Array of genres
    mpaa_rating = Column(
        String(10),
        nullable=True,
        # MPAA rating validation in check constraint below
    )
    
    # Content
    plot = Column(Text, nullable=True)  # Full plot summary
    director = Column(String(255), nullable=True)
    cast = Column(ARRAY(String), default=list)  # Array of primary cast members
    poster_url = Column(String(500), nullable=True)  # URL to poster image
    
    # Ratings
    imdb_rating = Column(
        Numeric(3, 1),
        nullable=True,
        # IMDb rating: 0.0-10.0
    )
    rt_rating = Column(
        Integer,
        nullable=True,
        # Rotten Tomatoes: 0-100 percentage
    )
    metacritic_rating = Column(
        Integer,
        nullable=True,
        # Metacritic: 0-100 score
    )
    
    # Awards
    awards_summary = Column(Text, nullable=True)  # e.g., "Won 4 Oscars"
    awards_count = Column(Integer, default=0)  # Total awards won
    nominations_count = Column(Integer, default=0)  # Total nominations
    awards_metadata = Column(JSONB, nullable=True)  # Detailed awards data (structured JSON)
    
    # Source tracking
    omdb_id = Column(String(50), unique=True, nullable=False)  # OMDb API identifier
    source = Column(String(20), default="omdb")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    content_score = relationship(
        "ContentScore", 
        back_populates="movie", 
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("year >= 1888 AND year <= 2100", name="check_year_range"),
        CheckConstraint(
            "mpaa_rating IN ('G', 'PG', 'PG-13', 'R', 'NC-17', 'Not Rated') OR mpaa_rating IS NULL",
            name="check_mpaa_rating"
        ),
        CheckConstraint(
            "imdb_rating >= 0 AND imdb_rating <= 10 OR imdb_rating IS NULL",
            name="check_imdb_rating"
        ),
        CheckConstraint(
            "rt_rating >= 0 AND rt_rating <= 100 OR rt_rating IS NULL",
            name="check_rt_rating"
        ),
        CheckConstraint(
            "metacritic_rating >= 0 AND metacritic_rating <= 100 OR metacritic_rating IS NULL",
            name="check_metacritic_rating"
        ),
    )
    
    def __repr__(self) -> str:
        return f"<Movie(id={self.id}, title='{self.title}', year={self.year})>"
