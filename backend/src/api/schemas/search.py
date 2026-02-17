"""Pydantic schemas for search filters"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class SearchFilters(BaseModel):
    """Search and filter parameters for movie queries"""
    
    # Text search
    q: Optional[str] = Field(None, description="Movie title search (partial or complete match)")
    
    # Traditional filters
    genres: Optional[List[str]] = Field(None, description="Filter by genre(s)")
    year_min: Optional[int] = Field(None, ge=1888, le=2100, description="Minimum release year")
    year_max: Optional[int] = Field(None, ge=1888, le=2100, description="Maximum release year")
    mpaa_ratings: Optional[List[str]] = Field(None, description="MPAA rating filter")
    imdb_min: Optional[float] = Field(None, ge=0, le=10, description="Minimum IMDb rating")
    rt_min: Optional[int] = Field(None, ge=0, le=100, description="Minimum Rotten Tomatoes rating")
    metacritic_min: Optional[int] = Field(None, ge=0, le=100, description="Minimum Metacritic rating")
    awards_min: Optional[int] = Field(None, ge=0, description="Minimum number of awards")
    
    # Content tolerance filters (0-10 or None for "any")
    sex_max: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Maximum sex/nudity content level (0-10, null = any)"
    )
    violence_max: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Maximum violence/gore content level (0-10, null = any)"
    )
    language_max: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Maximum language/profanity content level (0-10, null = any)"
    )
    
    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(30, ge=1, le=100, description="Results per page (1-100)")
    
    @validator('year_max')
    def year_max_must_be_gte_year_min(cls, v, values):
        """Ensure year_max >= year_min"""
        if 'year_min' in values and values['year_min'] is not None and v is not None:
            if v < values['year_min']:
                raise ValueError('year_max must be greater than or equal to year_min')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "q": "matrix",
                "genres": ["Action", "Sci-Fi"],
                "year_min": 1990,
                "year_max": 2010,
                "mpaa_ratings": ["PG-13", "R"],
                "imdb_min": 7.0,
                "sex_max": 5,
                "violence_max": 6,
                "language_max": 7,
                "page": 1,
                "per_page": 30
            }
        }
