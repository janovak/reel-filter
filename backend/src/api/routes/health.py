"""Health check API routes with database connectivity and refresh status"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, desc

from src.database.session import get_db
from src.models.data_refresh_log import DataRefreshLog

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.

    Returns:
    - Overall service status (healthy/degraded)
    - Database connectivity (connected/disconnected)
    - Last refresh timestamps for OMDb and Kids-in-Mind
    """
    health = {
        "status": "healthy",
        "database": "disconnected",
        "last_refresh": None,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health["status"] = "degraded"
        health["database"] = "disconnected"

    # Get last refresh timestamps
    try:
        last_omdb = (
            db.query(DataRefreshLog)
            .filter(DataRefreshLog.source == "omdb")
            .filter(DataRefreshLog.status.in_(["success", "partial"]))
            .order_by(desc(DataRefreshLog.refresh_date))
            .first()
        )

        last_kim = (
            db.query(DataRefreshLog)
            .filter(DataRefreshLog.source == "kids-in-mind")
            .filter(DataRefreshLog.status.in_(["success", "partial"]))
            .order_by(desc(DataRefreshLog.refresh_date))
            .first()
        )

        health["last_refresh"] = {
            "omdb": last_omdb.refresh_date.isoformat() + "Z" if last_omdb else None,
            "kids_in_mind": last_kim.refresh_date.isoformat() + "Z" if last_kim else None,
        }
    except Exception as e:
        logger.warning(f"Failed to fetch refresh timestamps: {e}")
        # Non-critical; don't degrade status for this

    return health
