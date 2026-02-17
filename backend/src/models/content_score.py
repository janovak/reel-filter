"""ContentScore model - Kids-in-Mind content ratings (0-10 scale)"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, 
    ForeignKey, Integer, Numeric, String, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database.base import Base


class ContentScore(Base):
    """Content ratings from Kids-in-Mind"""
    
    __tablename__ = "content_scores"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign key to Movie (one-to-one)
    movie_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("movies.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Content scores (0-10 scale)
    sex_nudity = Column(
        Integer,
        nullable=False,
        # 0 = minimal/no content, 10 = extreme content
    )
    violence_gore = Column(
        Integer,
        nullable=False,
    )
    language_profanity = Column(
        Integer,
        nullable=False,
    )
    
    # Source tracking
    source = Column(String(20), default="kids-in-mind")
    source_available = Column(Boolean, default=True)  # Flag for missing from source
    
    # Timestamps
    scraped_at = Column(DateTime, default=func.now())  # When content scores were scraped
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Fuzzy matching metadata
    match_confidence = Column(
        Numeric(5, 2),
        nullable=True
    )  # Confidence score 0-100
    manually_reviewed = Column(Boolean, default=False)  # Manual verification flag
    
    # Relationships
    movie = relationship("Movie", back_populates="content_score")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "sex_nudity >= 0 AND sex_nudity <= 10",
            name="check_sex_nudity_range"
        ),
        CheckConstraint(
            "violence_gore >= 0 AND violence_gore <= 10",
            name="check_violence_gore_range"
        ),
        CheckConstraint(
            "language_profanity >= 0 AND language_profanity <= 10",
            name="check_language_profanity_range"
        ),
        CheckConstraint(
            "match_confidence >= 0 AND match_confidence <= 100 OR match_confidence IS NULL",
            name="check_match_confidence_range"
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<ContentScore(id={self.id}, sex={self.sex_nudity}, "
            f"violence={self.violence_gore}, language={self.language_profanity})>"
        )
