"""SearchService - movie search and filtering logic"""
from typing import List, Tuple, Optional
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload

from src.models.movie import Movie
from src.models.content_score import ContentScore
from src.api.schemas.search import SearchFilters
from src.api.schemas.movie import MovieSchema, PaginationInfo
import math


class SearchService:
    """Service for searching and filtering movies"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_movies(
        self,
        filters: SearchFilters
    ) -> Tuple[List[Movie], PaginationInfo]:
        """
        Search movies with all filters applied.
        
        Core content filtering logic (FR-012, FR-014):
        - When ANY content threshold is set (not None), only movies WITH content scores are shown
        - Movies exceeding ANY threshold are filtered out
        - When ALL content thresholds are None, all movies are shown (with or without content scores)
        
        Args:
            filters: SearchFilters object with all filter parameters
            
        Returns:
            Tuple of (movies list, pagination info)
        """
        # Base query with eager loading of content_score relationship
        query = self.db.query(Movie).options(joinedload(Movie.content_score))
        
        # Content filtering logic
        has_content_filters = any([
            filters.sex_max is not None,
            filters.violence_max is not None,
            filters.language_max is not None
        ])
        
        if has_content_filters:
            # JOIN with content_scores (inner join to exclude movies without content scores)
            query = query.join(ContentScore, Movie.id == ContentScore.movie_id)
            
            # Apply content threshold filters
            if filters.sex_max is not None:
                query = query.filter(ContentScore.sex_nudity <= filters.sex_max)
            
            if filters.violence_max is not None:
                query = query.filter(ContentScore.violence_gore <= filters.violence_max)
            
            if filters.language_max is not None:
                query = query.filter(ContentScore.language_profanity <= filters.language_max)
        else:
            # No content filters active - use LEFT JOIN to include movies without content scores
            query = query.outerjoin(ContentScore, Movie.id == ContentScore.movie_id)
        
        # Title search (full-text search)
        if filters.q:
            query = query.filter(
                func.to_tsvector('english', Movie.title).match(
                    func.to_tsquery('english', filters.q)
                )
            )
        
        # Genre filtering (array overlap)
        if filters.genres and len(filters.genres) > 0:
            query = query.filter(Movie.genre.overlap(filters.genres))
        
        # Year range filtering
        if filters.year_min is not None:
            query = query.filter(Movie.year >= filters.year_min)
        if filters.year_max is not None:
            query = query.filter(Movie.year <= filters.year_max)
        
        # MPAA rating filtering
        if filters.mpaa_ratings and len(filters.mpaa_ratings) > 0:
            query = query.filter(Movie.mpaa_rating.in_(filters.mpaa_ratings))
        
        # Quality rating filters
        if filters.imdb_min is not None:
            query = query.filter(Movie.imdb_rating >= filters.imdb_min)
        if filters.rt_min is not None:
            query = query.filter(Movie.rt_rating >= filters.rt_min)
        if filters.metacritic_min is not None:
            query = query.filter(Movie.metacritic_rating >= filters.metacritic_min)
        
        # Awards filtering
        if filters.awards_min is not None:
            query = query.filter(Movie.awards_count >= filters.awards_min)
        
        # Get total count before pagination
        total = query.count()
        
        # Order by IMDb rating (highest first), then by year (newest first)
        query = query.order_by(Movie.imdb_rating.desc().nullslast(), Movie.year.desc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.per_page
        query = query.offset(offset).limit(filters.per_page)
        
        # Execute query
        movies = query.all()
        
        # Build pagination info
        total_pages = math.ceil(total / filters.per_page) if total > 0 else 0
        pagination = PaginationInfo(
            page=filters.page,
            per_page=filters.per_page,
            total=total,
            total_pages=total_pages,
            has_next=filters.page < total_pages,
            has_prev=filters.page > 1
        )
        
        return movies, pagination
    
    def get_movie_by_id(self, movie_id: str) -> Optional[Movie]:
        """
        Get a single movie by ID with content score.
        
        Args:
            movie_id: UUID of the movie
            
        Returns:
            Movie object or None if not found
        """
        return (
            self.db.query(Movie)
            .options(joinedload(Movie.content_score))
            .filter(Movie.id == movie_id)
            .first()
        )
