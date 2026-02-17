"""Metadata API routes - genre list and filter options"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.database.session import get_db
from src.models.movie import Movie

router = APIRouter()


@router.get("/genres")
async def get_genres(db: Session = Depends(get_db)):
    """
    Get all available genres from movies in the database.
    Returns a sorted, deduplicated list of genre strings.
    """
    # Unnest the genre arrays and get distinct values
    result = db.query(
        func.unnest(Movie.genre).label("genre")
    ).distinct().order_by("genre").all()

    genres = [row.genre for row in result if row.genre]

    return {"genres": genres}
