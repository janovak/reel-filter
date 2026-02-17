"""Pydantic schemas for movie responses"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class ContentScoreSchema(BaseModel):
    """Content score response schema"""
    id: UUID
    movie_id: UUID
    sex_nudity: int = Field(..., ge=0, le=10)
    violence_gore: int = Field(..., ge=0, le=10)
    language_profanity: int = Field(..., ge=0, le=10)
    source: str
    source_available: bool
    scraped_at: datetime
    updated_at: datetime
    match_confidence: Optional[float]
    manually_reviewed: bool
    
    class Config:
        from_attributes = True  # Allow ORM model conversion


class MovieSchema(BaseModel):
    """Movie response schema"""
    id: UUID
    title: str
    year: int
    runtime: Optional[int]
    genre: List[str]
    mpaa_rating: Optional[str]
    plot: Optional[str]
    director: Optional[str]
    cast: List[str]
    poster_url: Optional[str]
    imdb_rating: Optional[float]
    rt_rating: Optional[int]
    metacritic_rating: Optional[int]
    awards_summary: Optional[str]
    awards_count: int
    nominations_count: int
    awards_metadata: Optional[Dict[str, Any]]
    omdb_id: str
    source: str
    created_at: datetime
    updated_at: datetime
    content_score: Optional[ContentScoreSchema] = None
    
    class Config:
        from_attributes = True  # Allow ORM model conversion


class PaginationInfo(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1, le=100)
    total: int = Field(..., ge=0)
    total_pages: int = Field(..., ge=0)
    has_next: bool
    has_prev: bool


class SearchResponse(BaseModel):
    """Search results with pagination"""
    movies: List[MovieSchema]
    pagination: PaginationInfo
    
    class Config:
        schema_extra = {
            "example": {
                "movies": [
                    {
                        "id": "a1b2c3d4-e5f6-4789-0abc-def123456789",
                        "title": "The Matrix",
                        "year": 1999,
                        "runtime": 136,
                        "genre": ["Action", "Sci-Fi"],
                        "mpaa_rating": "R",
                        "plot": "A computer hacker learns from mysterious rebels...",
                        "director": "Lana Wachowski, Lilly Wachowski",
                        "cast": ["Keanu Reeves", "Laurence Fishburne"],
                        "poster_url": "https://example.com/poster.jpg",
                        "imdb_rating": 8.7,
                        "rt_rating": 87,
                        "metacritic_rating": 73,
                        "awards_summary": "Won 4 Oscars",
                        "awards_count": 42,
                        "nominations_count": 51,
                        "omdb_id": "tt0133093",
                        "source": "omdb",
                        "content_score": {
                            "sex_nudity": 3,
                            "violence_gore": 8,
                            "language_profanity": 5
                        }
                    }
                ],
                "pagination": {
                    "page": 1,
                    "per_page": 30,
                    "total": 150,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }
