"""Movies API routes"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database.session import get_db
from src.services.search_service import SearchService
from src.services.movie_service import MovieService
from src.api.schemas.search import SearchFilters
from src.api.schemas.movie import MovieSchema, MovieDetailSchema, SearchResponse

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_movies(
    filters: Annotated[SearchFilters, Query()],
    db: Session = Depends(get_db)
):
    """
    Search and filter movies.

    Content filtering logic:
    - When ANY content threshold is set (not null), only movies WITH content scores are returned
    - When ALL content thresholds are null, all movies are returned (with or without content scores)
    - Movies exceeding ANY threshold are filtered out

    Pagination: Returns 20-30 movies per page with pagination metadata

    `filters` is bound straight from the query string into SearchFilters (a
    FastAPI 0.115+ query parameter model), the same Filter Set shape the
    frontend's domain/filterSet.ts builds params from — one declaration of
    the 14 params instead of a signature and a reconstruction that must be
    kept in sync by hand.
    """
    # Execute search
    service = SearchService(db)
    movies, pagination = service.search_movies(filters)

    # Convert ORM models to Pydantic schemas
    movie_schemas = [MovieSchema.from_orm(movie) for movie in movies]

    return SearchResponse(movies=movie_schemas, pagination=pagination)


@router.get("/{movie_id}", response_model=MovieDetailSchema)
async def get_movie(
    movie_id: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive movie details by ID.
    Returns full movie metadata including plot, awards, timestamps, and content scores.
    """
    service = MovieService(db)
    movie = service.get_movie_by_id(movie_id)

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Movie not found",
                "message": f"No movie exists with ID: {movie_id}"
            }
        )

    return MovieDetailSchema.from_orm(movie)
