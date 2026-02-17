"""Movies API routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database.session import get_db
from src.services.search_service import SearchService
from src.api.schemas.search import SearchFilters
from src.api.schemas.movie import MovieSchema, SearchResponse

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_movies(
    q: str = None,
    genres: List[str] = None,
    year_min: int = None,
    year_max: int = None,
    mpaa_ratings: List[str] = None,
    imdb_min: float = None,
    rt_min: int = None,
    metacritic_min: int = None,
    awards_min: int = None,
    sex_max: int = None,
    violence_max: int = None,
    language_max: int = None,
    page: int = 1,
    per_page: int = 30,
    db: Session = Depends(get_db)
):
    """
    Search and filter movies.
    
    Content filtering logic:
    - When ANY content threshold is set (not null), only movies WITH content scores are returned
    - When ALL content thresholds are null, all movies are returned (with or without content scores)
    - Movies exceeding ANY threshold are filtered out
    
    Pagination: Returns 20-30 movies per page with pagination metadata
    """
    # Build filters object
    filters = SearchFilters(
        q=q,
        genres=genres,
        year_min=year_min,
        year_max=year_max,
        mpaa_ratings=mpaa_ratings,
        imdb_min=imdb_min,
        rt_min=rt_min,
        metacritic_min=metacritic_min,
        awards_min=awards_min,
        sex_max=sex_max,
        violence_max=violence_max,
        language_max=language_max,
        page=page,
        per_page=per_page
    )
    
    # Execute search
    service = SearchService(db)
    movies, pagination = service.search_movies(filters)
    
    # Convert ORM models to Pydantic schemas
    movie_schemas = [MovieSchema.from_orm(movie) for movie in movies]
    
    return SearchResponse(movies=movie_schemas, pagination=pagination)


@router.get("/{movie_id}", response_model=MovieSchema)
async def get_movie(
    movie_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a single movie by ID with content score.
    """
    service = SearchService(db)
    movie = service.get_movie_by_id(movie_id)
    
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found"
        )
    
    return MovieSchema.from_orm(movie)
