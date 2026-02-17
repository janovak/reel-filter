"""Database session and connection pooling"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

from src.database.base import Base


# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://reel_filter_user:dev_password_change_in_production@localhost:5432/reel_filter"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # Number of persistent connections
    max_overflow=10,  # Additional connections when pool is exhausted
    pool_pre_ping=True,  # Verify connections before using
    echo=os.getenv("DEBUG", "false").lower() == "true",  # SQL logging in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    
    Usage:
        @app.get("/movies")
        def get_movies(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
