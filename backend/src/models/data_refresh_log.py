"""DataRefreshLog model - operational tracking for weekly data refresh jobs"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from src.database.base import Base


class DataRefreshLog(Base):
    """Operational monitoring and auditing for weekly data refresh jobs"""
    
    __tablename__ = "data_refresh_logs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Refresh metadata
    refresh_date = Column(DateTime, nullable=False, default=func.now())
    source = Column(
        String(20),
        nullable=False,
        # Source: 'omdb' or 'kids-in-mind'
    )
    status = Column(
        String(20),
        nullable=False,
        # Status: 'success', 'failed', or 'partial'
    )
    
    # Statistics
    records_fetched = Column(Integer, default=0)  # Number retrieved from source
    records_updated = Column(Integer, default=0)  # Number updated in database
    records_created = Column(Integer, default=0)  # Number of new records created
    records_failed = Column(Integer, default=0)   # Number that failed to process
    
    # Error tracking
    errors = Column(JSONB, nullable=True)  # Structured error details (array of error objects)
    
    # Performance
    duration_seconds = Column(Integer, nullable=True)  # Job execution time
    completed_at = Column(DateTime, nullable=True)     # When job completed
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "source IN ('omdb', 'kids-in-mind')",
            name="check_source"
        ),
        CheckConstraint(
            "status IN ('success', 'failed', 'partial')",
            name="check_status"
        ),
    )
    
    def __repr__(self) -> str:
        return (
            f"<DataRefreshLog(id={self.id}, source='{self.source}', "
            f"status='{self.status}', date={self.refresh_date})>"
        )
